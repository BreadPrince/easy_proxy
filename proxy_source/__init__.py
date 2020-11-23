from .goubanjia import get_goubanjia
from .kuaidaili import get_kuaidaili
from .kxdaili import get_kxdaili

PROXY_SOURCE_LIST = [get_goubanjia, get_kuaidaili, get_kxdaili]
