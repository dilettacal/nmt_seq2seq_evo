import argparse
import time

import torch
import numpy as np

SEED = 1234
torch.manual_seed(SEED)
np.random.seed(SEED)

flatten = lambda l: [item for sublist in l for item in sublist]


def convert_time_unit(seconds):
    return time.strftime("%H:%M:%S", time.gmtime(seconds))


def str2number(param):
    try:
        number = int(param)
    except ValueError:
        number = float(param)
    return number


def str2bool(v):
    """
    Converts string boolean value to boolean value
    :param v: Value as string
    :return: True oder False
    """
    if v.lower() in ('yes', 'true', 't', 'y', '1'):
        return True
    elif v.lower() in ('no', 'false', 'f', 'n', '0'):
        return False
    else:
        raise argparse.ArgumentTypeError('Boolean value expected.')


SEED = 1234