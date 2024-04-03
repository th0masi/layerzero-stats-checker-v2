from enum import Enum


class SortType(Enum):
    SRCHAIN = "src_chains_list"
    PROTOCOL = "protocol_list"
    DSTCHAIN = "dst_chains_list"


class DataType(Enum):
    NUM_WALLETS = 1
    MIN_RANK = 2
    MAX_RANK = 3
    AVERAGE_RANK = 4
    TOTAL_VOLUME = 5
    TOP_500K = 6
    TOP_1KK = 7
    WITHOUT_MAINNET = 8
    ACTUAL_MONTH = 9
