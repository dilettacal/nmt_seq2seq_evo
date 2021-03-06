"""
Main script to preprocess datasets
The script automatically downloads the dataset from the Opus Platform: http://opus.nlpl.eu/Europarl.php
All TMX files are stored in the section "Statistics and TMX/Moses Downloads".
The upper right triangle contains the tmx files. The lower left triangle the corresponding text files.

Raw files should be extracted to: data/raw/europarl/<lang_code>
"""
import argparse
import os
import re
import time

from project.utils.data import custom_data_splits, persist_txt
from project.utils.external.tmx_to_text import Converter, FileOutput
from project.utils.utils_functions import str2number, convert_time_unit
from project.utils.utils_logging import Logger
from project.utils.utils_parsers import DatasetConfigParser
from project.utils.utils_retrieve_corpora import TmxCorpusDownloader, FileExtractor
from project.utils.utils_tokenizers import get_custom_tokenizer, SpacyTokenizer
from settings import DATA_DIR_RAW, DATA_DIR_PREPRO


def preprocess_single_dataset(config, lang_code, parser):
    """
    Preprocesses single dataset
    :param config: dataset config
    :param lang_code: langauge code (other than English)
    :param parser: arg parser
    """
    if lang_code == "en":
        raise SystemExit("English is the default language. Please provide second language!")
    if not lang_code:
        raise SystemExit("Empty language not allowed!")

    downloader = TmxCorpusDownloader(config, lang_code="fr")
    file_dir = downloader.download()
    file_extractor = FileExtractor(file_dir)
    file_extractor.extract()

    path_to_raw_file_dir = os.path.join(DATA_DIR_RAW, config.dataset_name, lang_code)
    path_to_tmx_file = [f for f in os.listdir(path_to_raw_file_dir) if f.endswith(".tmx")]
    assert len(path_to_tmx_file) == 1
    tmx_file_name = path_to_tmx_file[0]

    MAX_LEN, MIN_LEN = 30, 2  # min_len is by defaul 2 tokens

    file_name = lang_code + "-" + "en" + ".tmx"
    COMPLETE_PATH = os.path.join(path_to_raw_file_dir, tmx_file_name)
    print(COMPLETE_PATH)

    STORE_PATH = os.path.join(os.path.expanduser(DATA_DIR_PREPRO), config.dataset_name, lang_code, "splits", str(MAX_LEN))
    os.makedirs(STORE_PATH, exist_ok=True)

    start = time.time()
    output_file_path = os.path.join(DATA_DIR_PREPRO, config.dataset_name, lang_code)

    # Conversion tmx > text
    converter = Converter(output=FileOutput(output_file_path))
    converter.convert([COMPLETE_PATH])
    print("Converted lines:", converter.output_lines)
    print("Extraction took {} minutes to complete.".format(convert_time_unit(time.time() - start)))

    target_file = "bitext.{}".format(lang_code)
    src_lines, trg_lines = [], []

    # Read converted lines for further preprocessing
    with open(os.path.join(output_file_path, "bitext.en"), 'r', encoding="utf8") as src_file, \
            open(os.path.join(output_file_path, target_file), 'r', encoding="utf8") as target_file:
        for src_line, trg_line in zip(src_file, target_file):
            src_line = src_line.strip()
            trg_line = trg_line.strip()
            if src_line != "" and trg_line != "":
                src_lines.append(src_line)
                trg_lines.append(trg_line)

    ### tokenize lines ####
    assert len(src_lines) == len(trg_lines), "Lines should have the same lengths."

    TOKENIZATION_MODE = "w"
    PREPRO_PHASE = True
    # Get tokenizer
    src_tokenizer, trg_tokenizer = get_custom_tokenizer("en", TOKENIZATION_MODE, prepro=PREPRO_PHASE), \
                                   get_custom_tokenizer(lang_code, TOKENIZATION_MODE, prepro=PREPRO_PHASE)

    # Creates logger to log tokenized objects
    src_logger = Logger(output_file_path, file_name="bitext.tok.en")
    trg_logger = Logger(output_file_path, file_name="bitext.tok.{}".format(lang_code))

    temp_src_toks, temp_trg_toks = [], []

    # Start the tokenisation process
    if isinstance(src_tokenizer, SpacyTokenizer):
        print("\nTokenization for source sequences is performed with spaCy")
        with src_tokenizer.nlp.disable_pipes('ner'):
            for i, doc in enumerate(src_tokenizer.nlp.pipe(src_lines, batch_size=1000)):
                tok_doc = ' '.join([tok.text for tok in doc])
                temp_src_toks.append(tok_doc)
                src_logger.log(tok_doc, stdout=True if i % 100000 == 0 else False)
    else:
        print("\nTokenization for source sequences is performed with FastTokenizer")
        for i, sent in enumerate(src_lines):
            tok_sent = src_tokenizer.tokenize(sent)
            tok_sent = ' '.join(tok_sent)
            temp_src_toks.append(tok_sent)
            src_logger.log(tok_sent, stdout=True if i % 100000 == 0 else False)

    if isinstance(trg_tokenizer, SpacyTokenizer):
        print("\nTokenization for target sequences is performed with spaCy")
        with trg_tokenizer.nlp.disable_pipes('ner'):
            for i, doc in enumerate(trg_tokenizer.nlp.pipe(trg_lines, batch_size=1000)):
                tok_doc = ' '.join([tok.text for tok in doc])
                temp_trg_toks.append(tok_doc)
                trg_logger.log(tok_doc, stdout=True if i % 100000 == 0 else False)
    else:
        print("\nTokenization for target sequences is performed with FastTokenizer")
        for i, sent in enumerate(trg_lines):
            tok_sent = trg_tokenizer.tokenize(sent)
            tok_sent = ' '.join(tok_sent)
            temp_src_toks.append(tok_sent)
            src_logger.log(tok_sent, stdout=True if i % 100000 == 0 else False)

    # Reduce lines by max_len
    filtered_src_lines, filtered_trg_lines = [], []
    print("Reducing corpus to sequences of min length {} max length: {}".format(MIN_LEN, MAX_LEN))

    filtered_src_lines, filtered_trg_lines = [], []
    for src_l, trg_l in zip(temp_src_toks, temp_trg_toks):
        ### remove possible duplicate spaces
        src_l_s = re.sub(' +', ' ', src_l)
        trg_l_s = re.sub(' +', ' ', trg_l)
        if src_l_s != "" and trg_l_s != "":
            src_l_spl, trg_l_spl = src_l_s.split(" "), trg_l_s.split(" ")
            if len(src_l_spl) <= MAX_LEN and len(trg_l_spl) <= MAX_LEN:
                if len(src_l_spl) >= MIN_LEN and len(trg_l_spl) >= MIN_LEN:
                    filtered_src_lines.append(' '.join(src_l_spl))
                    filtered_trg_lines.append(' '.join(trg_l_spl))

        assert len(filtered_src_lines) == len(filtered_trg_lines)

    src_lines, trg_lines = filtered_src_lines, filtered_trg_lines
    print("Splitting files...")
    train_data, val_data, test_data, samples_data = custom_data_splits(src_lines, trg_lines,
                                                                       val_samples=parser.test_ratio)
    persist_txt(train_data, STORE_PATH, "train.tok", exts=(".en", "." + lang_code))
    persist_txt(val_data, STORE_PATH, "val.tok", exts=(".en", "." + lang_code))
    persist_txt(test_data, STORE_PATH, "test.tok", exts=(".en", "." + lang_code))
    if lang_code != "de":  # for german language sample files are versioned with the program
        print("Generating samples files...")
        persist_txt(samples_data, STORE_PATH, file_name="samples.tok", exts=(".en", "." + lang_code))

    print("Total time:", convert_time_unit(time.time() - start))


def data_prepro_parser():
    """
    Arg parser
    :return: parsed args
    """
    parser = argparse.ArgumentParser(
        description='Preprocess Europarl Dataset for NMT. \nThis script allows you to preprocess and tokenize the Europarl Dataset.')
    parser.add_argument("--dataset", nargs='+', default="europarl", type=str)
    parser.add_argument("--lang_code", default="de", type=str,
                        help="First language is English. Specifiy with 'lang_code' the second language as language code (e.g. 'de').")
    parser.add_argument("--test_ratio", help="Specify the test ratio. Standard: 3000 samples. If you pass a float, this will be split the data based on that proportion, e.g. 0.1 --> 0.8, 0.1, 0.1",
                        type=str2number, default=3000)
    return parser


if __name__ == '__main__':
    parser = data_prepro_parser().parse_args()
    CORPUS = parser.dataset
    lang_code = parser.lang_code.lower()
    # get corpus config
    config = DatasetConfigParser(CORPUS)
    # preprocess corpus
    preprocess_single_dataset(config, lang_code, parser)
