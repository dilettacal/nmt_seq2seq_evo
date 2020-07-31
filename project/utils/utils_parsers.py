import os
from configparser import ConfigParser, NoSectionError
from pathlib import Path
from settings import CONFIG_PATH


class DatasetConfigParser(object):
    # config/datasets.cfg
    def __init__(self, dataset_name):
        self.config_path = Path(CONFIG_PATH) / "datasets.cfg"
        self.parser = ConfigParser()
        self.parser.read(self.config_path)
        self.dataset_name = dataset_name
        assert self.dataset_name.strip().lower() in self.parser.sections(), \
            "Provide valid dataset name!"

    def get_dataset_url(self):
        return os.path.join(self.parser.get(self.dataset_name.strip().lower(), "url"),
                                self.parser.get(self.dataset_name.strip().lower(), "version"),
                                "tmx")

    def get_download_dir(self):
        return self.parser.get(self.dataset_name.strip().lower(), "download_dir")

#TODO: Use this parser to load spacy models!
class LanguageModelConfigParser(object):
    # config/lm.cfg
    def __init__(self):
        self.config_path = Path(CONFIG_PATH) / "lm.cfg"
        self.parser = ConfigParser()
        self.parser.read(self.config_path)

    def get_language_model(self, lang_code):
        languages_section = "LANGUAGES"
        try:
            if lang_code in list(self.parser.items(languages_section)):
                return "lang specific model {}".format(self.parser.get(languages_section, lang_code))
            else:
                return "multi-lang model {}".format(self.parser.get("MULTI", "xx"))
        except NoSectionError:
            return "Please check your configuration file! " \
                   "Section of available language models {} is missing!".format(languages_section)

    def get_pretrained_embedding_url(self, embedding, lang_code):
        embedding_section = embedding.strip().upper()
        print(embedding_section)
        try:
            return self.parser.get(embedding_section, embedding_section.lower()).format(lang_code)
        except NoSectionError:
            return "{} not available in config file!".format(embedding_section)