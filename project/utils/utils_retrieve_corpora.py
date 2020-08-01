import gzip
import os
import shutil
import tarfile
import urllib.error
import urllib.request
import zipfile
from pathlib import Path
from urllib.error import ContentTooShortError

from project.utils.external.download import _print_download_progress
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
                    split =urllib.parse.urlsplit(url)
                    file = split.query.split("/")[-1]
                    final_destination = os.path.join(self.download_directory, file)
                    urllib.request.urlretrieve(url, final_destination, reporthook=_print_download_progress)
                    print("\nCorpus downloaded in {}".format(self.download_directory))
                    download = True
                except (urllib.error.URLError or ContentTooShortError) as e:
                    #http://opus.nlpl.eu/download.php?f=Europarl/v8/tmx/en-fr.tmx.gz
                    print(e)
                    continue
        else:
            print("File already downloaded in {}".format(self.download_directory))

        return self.download_directory
