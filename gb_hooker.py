from pyboy import PyBoy, PyBoyRegisterFile
from symbol_parser import parse_sym_file
import asyncio

from consts import *

class GBHooker:
    pyboy: PyBoy
    queue: asyncio.Queue
    def __init__(self, _pyboy : PyBoy, symbol_dict: dict):
        self.pyboy = _pyboy
        self.symbol_dict = symbol_dict
    
    def initHooks(self, queue: asyncio.Queue):
        self.pyboy.hook_register(self.symbol_dict["PlaceString"][0], self.symbol_dict["PlaceString"][1], self.PlaceStringHook, self.pyboy.register_file)
        self.queue = queue
    
    def PlaceStringHook(self, pyboyregisterfile: PyBoyRegisterFile):
        loop = asyncio.get_event_loop()
        strptr = (pyboyregisterfile.D << 8) + pyboyregisterfile.E
        winpos = pyboyregisterfile.HL
        if(winpos == 50361):
            print(winpos)
            i = 0
            rawcodes = ''
            while not (self.pyboy.memory[strptr+i] == 0x50 or self.pyboy.memory[strptr+i] == 0x57 
                       or self.pyboy.memory[strptr+i] == 0x00): #terminate char
                if self.pyboy.memory[strptr+i] in CHARMAP:
                    rawcodes += CHARMAP[self.pyboy.memory[strptr+i]]
                i = i + 1
            print(rawcodes)
            asyncio.ensure_future(self.queue.put(rawcodes), loop = loop)

        
        



    