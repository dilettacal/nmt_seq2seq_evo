import gzip
import os
import shutil
import sys
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from urllib.error import ContentTooShortError
from project.utils.utils_parsers import DatasetConfigParser


class TmxCorpusDownloader(object):
    def __init__(self, config: DatasetConfigParser, lang_code="de"):
        self.url = config.get_dataset_url()
        assert "tmx" in self.url, "Only TMX corpora supported!"
        self.lang_code = lang_code
        self.download_directory = Path(config.get_download_dir() / Path(self.lang_code))
        self.full_url = [
            os.path.join(self.url, "en-{}.tmx.gz".format(self.lang_code)),
            os.path.join(self.url, "{}-en.tmx.gz".format(self.lang_code))
        ]

    def download(self):
        os.makedirs(self.download_directory, exist_ok=True)
        file_endings = (".gz", ".tar", ".zip")
        already_downloaded = [e for e in self.download_directory.iterdir() if e.is_file()
                              and (e.name.endswith(file_endings))]
        download = False
        if not already_downloaded:
            for url in self.full_url:
                if download:
                    break
                try:
                    split = urllib.parse.urlsplit(url)
                    file = split.query.split("/")[-1]
                    final_destination = os.path.join(self.download_directory, file)
                    urllib.request.urlretrieve(url, final_destination, reporthook=_print_download_progress)
                    print("\nCorpus downloaded in {}".format(self.download_directory))
                    download = True
                except (urllib.error.URLError or ContentTooShortError) as e:
                    # http://opus.nlpl.eu/download.php?f=Europarl/v8/tmx/en-fr.tmx.gz
                    print(e)
                    continue
        else:
            print("File already downloaded in {}".format(self.download_directory))

        return self.download_directory


class FileExtractor():
    def __init__(self, file_dir):
        self.file_dir = file_dir

    def extract(self):
        already_extracted = [e for e in self.file_dir.iterdir() if e.is_file()
                             and (e.name.endswith(".tmx"))]
        if not already_extracted:
            file_endings = (".gz", ".tar", ".zip")
            file_path = [e for e in self.file_dir.iterdir() if e.is_file()
                         and (e.name.endswith(file_endings))]
            assert len(file_path) == 1
            path_to_compressed_file = str(file_path[0])
            path_to_tmx_file = '' + path_to_compressed_file.split(".tmx")[0] + '.tmx'

            # extract file
            if path_to_compressed_file.endswith(".zip"):
                zipfile.ZipFile(file=path_to_compressed_file, mode="r").extractall(self.file_dir)
            elif path_to_compressed_file.endswith((".tar.gz", ".tgz")):
                tarfile.open(name=path_to_compressed_file, mode="r:gz").extractall(self.file_dir)
            elif path_to_compressed_file.endswith(".gz"):
                # Modified for tmx files #
                with gzip.open(path_to_compressed_file, 'rb') as gz:
                    with open(path_to_tmx_file, 'wb') as uncompressed:
                        shutil.copyfileobj(gz, uncompressed)
            print("File extracted!")
        else:
            print("File already extracted!")
        return True


def _print_download_progress(count, block_size, total_size):
    """
    Function used for printing the download progress.
    Used as a call-back function in maybe_download_and_extract().
    # https://github.com/Hvass-Labs/TensorFlow-Tutorials
    # Copyright 2016 by Magnus Erik Hvass Pedersen
    """
    # Percentage completion.
    pct_complete = float(count * block_size) / total_size
    # Limit it because rounding errors may cause it to exceed 100%.
    pct_complete = min(1.0, pct_complete)
    # Status-message. Note the \r which means the line should overwrite itself.
    msg = "\r- Download progress: {0:.1%}".format(pct_complete)
    # Print it.
    sys.stdout.write(msg)
    sys.stdout.flush()