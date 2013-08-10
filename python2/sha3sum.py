#!/usr/bin/env python2
# -*- coding: utf-8 -*-
'''
sha3sum – SHA-3 (Keccak) checksum calculator

Copyright © 2013  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.
'''

import sys
import os


stdout = os.fdopen(1, 'w')
stderr = os.fdopen(2, 'w')


def printerr(text, end = '\n'):
    stderr.write(text + end)
    stderr.flush()


def write(data):
    stdout.write(data)


def flush():
    stdout.flush()


class SHA3:
    '''
    SHA-3/Keccak hash algorithm implementation
    
    @author  Mattias Andrée  (maandree@member.fsf.org)
    '''
    
    
    RC = [0x0000000000000001, 0x0000000000008082, 0x800000000000808A, 0x8000000080008000,
          0x000000000000808B, 0x0000000080000001, 0x8000000080008081, 0x8000000000008009,
          0x000000000000008A, 0x0000000000000088, 0x0000000080008009, 0x000000008000000A,
          0x000000008000808B, 0x800000000000008B, 0x8000000000008089, 0x8000000000008003,
          0x8000000000008002, 0x8000000000000080, 0x000000000000800A, 0x800000008000000A,
          0x8000000080008081, 0x8000000000008080, 0x0000000080000001, 0x8000000080008008]
    '''
    :list<int>  Round contants
    '''
    
    B = [0] * 25
    '''
    :list<int>  Keccak-f round temporary
    '''
    
    C = [0] * 5
    '''
    :list<int>  Keccak-f round temporary
    '''
    

    (r, c, n, b, w, wmod, l, nr) = (0, 0, 0, 0, 0, 0, 0, 0)
    '''
       r:int  The bitrate
       c:int  The capacity
       n:int  The output size
       b:int  The state size
       w:int  The word size
    wmod:int  The word mask
       l:int  ℓ, the binary logarithm of the word size
      nr:int  12 + 2ℓ, the number of rounds
    '''
    
    S = None
    '''
    :list<int>  The current state
    '''
    
    M = None
    '''
    :bytes  Left over water to fill the sponge with at next update
    '''
    
    
    
    @staticmethod
    def rotate(x, n):
        '''
        Rotate a word
        
        @param   x:int  The value to rotate
        @param   n:int  Rotation steps
        @return   :int  The value rotated
        '''
        m = n % SHA3.w
        return ((x >> (SHA3.w - m)) + (x << m)) & SHA3.wmod
    
    
    @staticmethod
    def rotate64(x, n):
        '''
        Rotate a 64-bit word
        
        @param   x:int  The value to rotate
        @param   n:int  Rotation steps
        @return   :int  The value rotated
        '''
        return ((x >> (64 - n)) + (x << n)) & 0xFFFFFFFFFFFFFFFF
    
    
    @staticmethod
    def lb(x):
        '''
        Binary logarithm
        
        @param   x:int  The value of which to calculate the binary logarithm
        @return   :int  The binary logarithm
        '''
        rc = 0
        if (x & 0xFF00) != 0:  rc +=  8 ;  x >>=  8
        if (x & 0x00F0) != 0:  rc +=  4 ;  x >>=  4
        if (x & 0x000C) != 0:  rc +=  2 ;  x >>=  2
        if (x & 0x0002) != 0:  rc +=  1
        return rc
    
    
    @staticmethod
    def keccakFRound(A, rc):
        '''
        Perform one round of computation
        
        @param   A:list<int>  The current state
        @param  rc:int        Round constant
        '''
        if SHA3.w == 64:
            # θ step (step 1 and 2 of 3)
            SHA3.C[0] = (A[0]  ^ A[1])  ^ (A[2]  ^ A[3])  ^ A[4]
            SHA3.C[2] = (A[10] ^ A[11]) ^ (A[12] ^ A[13]) ^ A[14]
            db = SHA3.C[0] ^ SHA3.rotate64(SHA3.C[2], 1)
            SHA3.C[4] = (A[20] ^ A[21]) ^ (A[22] ^ A[23]) ^ A[24]
            dd = SHA3.C[2] ^ SHA3.rotate64(SHA3.C[4], 1)
            SHA3.C[1] = (A[5]  ^ A[6])  ^ (A[7]  ^ A[8])  ^ A[9]
            da = SHA3.C[4] ^ SHA3.rotate64(SHA3.C[1], 1)
            SHA3.C[3] = (A[15] ^ A[16]) ^ (A[17] ^ A[18]) ^ A[19]
            dc = SHA3.C[1] ^ SHA3.rotate64(SHA3.C[3], 1)
            de = SHA3.C[3] ^ SHA3.rotate64(SHA3.C[0], 1)
            
            # ρ and π steps, with last part of θ
            SHA3.B[0] = SHA3.rotate64(A[0] ^ da, 0)
            SHA3.B[1] = SHA3.rotate64(A[15] ^ dd, 28)
            SHA3.B[2] = SHA3.rotate64(A[5] ^ db, 1)
            SHA3.B[3] = SHA3.rotate64(A[20] ^ de, 27)
            SHA3.B[4] = SHA3.rotate64(A[10] ^ dc, 62)
            
            SHA3.B[5] = SHA3.rotate64(A[6] ^ db, 44)
            SHA3.B[6] = SHA3.rotate64(A[21] ^ de, 20)
            SHA3.B[7] = SHA3.rotate64(A[11] ^ dc, 6)
            SHA3.B[8] = SHA3.rotate64(A[1] ^ da, 36)
            SHA3.B[9] = SHA3.rotate64(A[16] ^ dd, 55)
            
            SHA3.B[10] = SHA3.rotate64(A[12] ^ dc, 43)
            SHA3.B[11] = SHA3.rotate64(A[2] ^ da, 3)
            SHA3.B[12] = SHA3.rotate64(A[17] ^ dd, 25)
            SHA3.B[13] = SHA3.rotate64(A[7] ^ db, 10)
            SHA3.B[14] = SHA3.rotate64(A[22] ^ de, 39)
            
            SHA3.B[15] = SHA3.rotate64(A[18] ^ dd, 21)
            SHA3.B[16] = SHA3.rotate64(A[8] ^ db, 45)
            SHA3.B[17] = SHA3.rotate64(A[23] ^ de, 8)
            SHA3.B[18] = SHA3.rotate64(A[13] ^ dc, 15)
            SHA3.B[19] = SHA3.rotate64(A[3] ^ da, 41)
            
            SHA3.B[20] = SHA3.rotate64(A[24] ^ de, 14)
            SHA3.B[21] = SHA3.rotate64(A[14] ^ dc, 61)
            SHA3.B[22] = SHA3.rotate64(A[4] ^ da, 18)
            SHA3.B[23] = SHA3.rotate64(A[19] ^ dd, 56)
            SHA3.B[24] = SHA3.rotate64(A[9] ^ db, 2)
        else:
            # θ step (step 1 and 2 of 3)
            SHA3.C[0] = (A[0]  ^ A[1])  ^ (A[2]  ^ A[3])  ^ A[4]
            SHA3.C[2] = (A[10] ^ A[11]) ^ (A[12] ^ A[13]) ^ A[14]
            db = SHA3.C[0] ^ SHA3.rotate(SHA3.C[2], 1)
            SHA3.C[4] = (A[20] ^ A[21]) ^ (A[22] ^ A[23]) ^ A[24]
            dd = SHA3.C[2] ^ SHA3.rotate(SHA3.C[4], 1)
            SHA3.C[1] = (A[5]  ^ A[6])  ^ (A[7]  ^ A[8])  ^ A[9]
            da = SHA3.C[4] ^ SHA3.rotate(SHA3.C[1], 1)
            SHA3.C[3] = (A[15] ^ A[16]) ^ (A[17] ^ A[18]) ^ A[19]
            dc = SHA3.C[1] ^ SHA3.rotate(SHA3.C[3], 1)
            de = SHA3.C[3] ^ SHA3.rotate(SHA3.C[0], 1)
            
            # ρ and π steps, with last part of θ
            SHA3.B[0] = SHA3.rotate(A[0] ^ da, 0)
            SHA3.B[1] = SHA3.rotate(A[15] ^ dd, 28)
            SHA3.B[2] = SHA3.rotate(A[5] ^ db, 1)
            SHA3.B[3] = SHA3.rotate(A[20] ^ de, 27)
            SHA3.B[4] = SHA3.rotate(A[10] ^ dc, 62)
            
            SHA3.B[5] = SHA3.rotate(A[6] ^ db, 44)
            SHA3.B[6] = SHA3.rotate(A[21] ^ de, 20)
            SHA3.B[7] = SHA3.rotate(A[11] ^ dc, 6)
            SHA3.B[8] = SHA3.rotate(A[1] ^ da, 36)
            SHA3.B[9] = SHA3.rotate(A[16] ^ dd, 55)
            
            SHA3.B[10] = SHA3.rotate(A[12] ^ dc, 43)
            SHA3.B[11] = SHA3.rotate(A[2] ^ da, 3)
            SHA3.B[12] = SHA3.rotate(A[17] ^ dd, 25)
            SHA3.B[13] = SHA3.rotate(A[7] ^ db, 10)
            SHA3.B[14] = SHA3.rotate(A[22] ^ de, 39)
            
            SHA3.B[15] = SHA3.rotate(A[18] ^ dd, 21)
            SHA3.B[16] = SHA3.rotate(A[8] ^ db, 45)
            SHA3.B[17] = SHA3.rotate(A[23] ^ de, 8)
            SHA3.B[18] = SHA3.rotate(A[13] ^ dc, 15)
            SHA3.B[19] = SHA3.rotate(A[3] ^ da, 41)
            
            SHA3.B[20] = SHA3.rotate(A[24] ^ de, 14)
            SHA3.B[21] = SHA3.rotate(A[14] ^ dc, 61)
            SHA3.B[22] = SHA3.rotate(A[4] ^ da, 18)
            SHA3.B[23] = SHA3.rotate(A[19] ^ dd, 56)
            SHA3.B[24] = SHA3.rotate(A[9] ^ db, 2)
        
        # ξ step
        A[0] = SHA3.B[0] ^ ((~(SHA3.B[5])) & SHA3.B[10])
        A[1] = SHA3.B[1] ^ ((~(SHA3.B[6])) & SHA3.B[11])
        A[2] = SHA3.B[2] ^ ((~(SHA3.B[7])) & SHA3.B[12])
        A[3] = SHA3.B[3] ^ ((~(SHA3.B[8])) & SHA3.B[13])
        A[4] = SHA3.B[4] ^ ((~(SHA3.B[9])) & SHA3.B[14])
        
        A[5] = SHA3.B[5] ^ ((~(SHA3.B[10])) & SHA3.B[15])
        A[6] = SHA3.B[6] ^ ((~(SHA3.B[11])) & SHA3.B[16])
        A[7] = SHA3.B[7] ^ ((~(SHA3.B[12])) & SHA3.B[17])
        A[8] = SHA3.B[8] ^ ((~(SHA3.B[13])) & SHA3.B[18])
        A[9] = SHA3.B[9] ^ ((~(SHA3.B[14])) & SHA3.B[19])
        
        A[10] = SHA3.B[10] ^ ((~(SHA3.B[15])) & SHA3.B[20])
        A[11] = SHA3.B[11] ^ ((~(SHA3.B[16])) & SHA3.B[21])
        A[12] = SHA3.B[12] ^ ((~(SHA3.B[17])) & SHA3.B[22])
        A[13] = SHA3.B[13] ^ ((~(SHA3.B[18])) & SHA3.B[23])
        A[14] = SHA3.B[14] ^ ((~(SHA3.B[19])) & SHA3.B[24])
        
        A[15] = SHA3.B[15] ^ ((~(SHA3.B[20])) & SHA3.B[0])
        A[16] = SHA3.B[16] ^ ((~(SHA3.B[21])) & SHA3.B[1])
        A[17] = SHA3.B[17] ^ ((~(SHA3.B[22])) & SHA3.B[2])
        A[18] = SHA3.B[18] ^ ((~(SHA3.B[23])) & SHA3.B[3])
        A[19] = SHA3.B[19] ^ ((~(SHA3.B[24])) & SHA3.B[4])
        
        A[20] = SHA3.B[20] ^ ((~(SHA3.B[0])) & SHA3.B[5])
        A[21] = SHA3.B[21] ^ ((~(SHA3.B[1])) & SHA3.B[6])
        A[22] = SHA3.B[22] ^ ((~(SHA3.B[2])) & SHA3.B[7])
        A[23] = SHA3.B[23] ^ ((~(SHA3.B[3])) & SHA3.B[8])
        A[24] = SHA3.B[24] ^ ((~(SHA3.B[4])) & SHA3.B[9])
        
        # ι step
        A[0] ^= rc
    
    
    @staticmethod
    def keccakF(A):
        '''
        Perform Keccak-f function
        
        @param  A:list<int>  The current state
        '''
        if (SHA3.nr == 24):
            SHA3.keccakFRound(A, 0x0000000000000001)
            SHA3.keccakFRound(A, 0x0000000000008082)
            SHA3.keccakFRound(A, 0x800000000000808A)
            SHA3.keccakFRound(A, 0x8000000080008000)
            SHA3.keccakFRound(A, 0x000000000000808B)
            SHA3.keccakFRound(A, 0x0000000080000001)
            SHA3.keccakFRound(A, 0x8000000080008081)
            SHA3.keccakFRound(A, 0x8000000000008009)
            SHA3.keccakFRound(A, 0x000000000000008A)
            SHA3.keccakFRound(A, 0x0000000000000088)
            SHA3.keccakFRound(A, 0x0000000080008009)
            SHA3.keccakFRound(A, 0x000000008000000A)
            SHA3.keccakFRound(A, 0x000000008000808B)
            SHA3.keccakFRound(A, 0x800000000000008B)
            SHA3.keccakFRound(A, 0x8000000000008089)
            SHA3.keccakFRound(A, 0x8000000000008003)
            SHA3.keccakFRound(A, 0x8000000000008002)
            SHA3.keccakFRound(A, 0x8000000000000080)
            SHA3.keccakFRound(A, 0x000000000000800A)
            SHA3.keccakFRound(A, 0x800000008000000A)
            SHA3.keccakFRound(A, 0x8000000080008081)
            SHA3.keccakFRound(A, 0x8000000000008080)
            SHA3.keccakFRound(A, 0x0000000080000001)
            SHA3.keccakFRound(A, 0x8000000080008008)
        else:
            for i in range(SHA3.nr):
                SHA3.keccakFRound(A, SHA3.RC[i] & SHA3.wmod)
    
    
    @staticmethod
    def toLane(message, rr, ww, off):
        '''
        Convert a chunk of char:s to a word
        
        @param   message:bytes  The message
        @param        rr:int    Bitrate in bytes
        @param        ww:int    Word size in bytes
        @param       off:int    The offset in the message
        @return         :int    Lane
        '''
        rc = 0
        i = off + ww - 1
        n = min(len(message), rr)
        while i >= off:
            rc = (rc << 8) | (message[i] if (i < n) else 0)
            i -= 1
        return rc
    
    
    @staticmethod
    def toLane64(message, rr, off):
        '''
        Convert a chunk of char:s to a 64-bit word
        
        @param   message:bytes  The message
        @param        rr:int    Bitrate in bytes
        @param       off:int    The offset in the message
        @return         :int    Lane
        '''
        n = min(len(message), rr)
        
        return ((message[off + 7] << 56) if (off + 7 < n) else 0) | \
               ((message[off + 6] << 48) if (off + 6 < n) else 0) | \
               ((message[off + 5] << 40) if (off + 5 < n) else 0) | \
               ((message[off + 4] << 32) if (off + 4 < n) else 0) | \
               ((message[off + 3] << 24) if (off + 3 < n) else 0) | \
               ((message[off + 2] << 16) if (off + 2 < n) else 0) | \
               ((message[off + 1] <<  8) if (off + 1 < n) else 0) | \
               ((message[off]) if (off < n) else 0)
    
    
    @staticmethod
    def pad10star1(msg, r):
        '''
        pad 10*1
        
        @param   msg:bytes  The message to pad
        @param     r:int    The bitrate
        @return     :str    The message padded
        '''
        nnn = len(msg) << 3
        
        nrf = nnn >> 3
        nbrf = nnn & 7
        ll = nnn % r
        
        bbbb = 1 if nbrf == 0 else ((msg[nrf] >> (8 - nbrf)) | (1 << nbrf))
        
        message = None
        if ((r - 8 <= ll) and (ll <= r - 2)):
            message = [bbbb ^ 128]
        else:
            nnn = (nrf + 1) << 3
            nnn = ((nnn - (nnn % r) + (r - 8)) >> 3) + 1
            message = [0] * (nnn - nrf)
            message[0] = bbbb
            nnn -= nrf
            message[nnn - 1] = 0x80
        
        return msg[:nrf] + message
    
    
    @staticmethod
    def initialise(r, c, n):
        '''
        Initialise Keccak sponge
        
        @param  r:int  The bitrate
        @param  c:int  The capacity
        @param  n:int  The output size
        '''
        SHA3.r = r
        SHA3.c = c
        SHA3.n = n
        SHA3.b = r + c
        SHA3.w = SHA3.b // 25
        SHA3.l = SHA3.lb(SHA3.w)
        SHA3.nr = 12 + (SHA3.l << 1)
        SHA3.wmod = (1 << SHA3.w) - 1
        SHA3.S = [0] * 25
        SHA3.M = []
    
    
    @staticmethod
    def update(msg, msglen = None):
        '''
        Absorb the more of the message message to the Keccak sponge
        
        @param  msg:bytes   The partial message
        @param  msglen:int  The length of the partial message
        '''
        if msglen is not None:
            msg = msg[:msglen]
        
        rr = SHA3.r >> 3
        ww = SHA3.w >> 3
        
        SHA3.M += msg
        nnn = len(SHA3.M)
        nnn -= nnn % ((SHA3.r * SHA3.b) >> 3)
        message = SHA3.M[:nnn]
        SHA3.M = SHA3.M[nnn:]
        
        # Absorbing phase
        if ww == 8:
            for i in range(0, nnn, rr):
                SHA3.S[ 0] ^= SHA3.toLane64(message, rr, 0)
                SHA3.S[ 5] ^= SHA3.toLane64(message, rr, 8)
                SHA3.S[10] ^= SHA3.toLane64(message, rr, 16)
                SHA3.S[15] ^= SHA3.toLane64(message, rr, 24)
                SHA3.S[20] ^= SHA3.toLane64(message, rr, 32)
                SHA3.S[ 1] ^= SHA3.toLane64(message, rr, 40)
                SHA3.S[ 6] ^= SHA3.toLane64(message, rr, 48)
                SHA3.S[11] ^= SHA3.toLane64(message, rr, 56)
                SHA3.S[16] ^= SHA3.toLane64(message, rr, 64)
                SHA3.S[21] ^= SHA3.toLane64(message, rr, 72)
                SHA3.S[ 2] ^= SHA3.toLane64(message, rr, 80)
                SHA3.S[ 7] ^= SHA3.toLane64(message, rr, 88)
                SHA3.S[12] ^= SHA3.toLane64(message, rr, 96)
                SHA3.S[17] ^= SHA3.toLane64(message, rr, 104)
                SHA3.S[22] ^= SHA3.toLane64(message, rr, 112)
                SHA3.S[ 3] ^= SHA3.toLane64(message, rr, 120)
                SHA3.S[ 8] ^= SHA3.toLane64(message, rr, 128)
                SHA3.S[13] ^= SHA3.toLane64(message, rr, 136)
                SHA3.S[18] ^= SHA3.toLane64(message, rr, 144)
                SHA3.S[23] ^= SHA3.toLane64(message, rr, 152)
                SHA3.S[ 4] ^= SHA3.toLane64(message, rr, 160)
                SHA3.S[ 9] ^= SHA3.toLane64(message, rr, 168)
                SHA3.S[14] ^= SHA3.toLane64(message, rr, 176)
                SHA3.S[19] ^= SHA3.toLane64(message, rr, 184)
                SHA3.S[24] ^= SHA3.toLane64(message, rr, 192)
                SHA3.keccakF(SHA3.S)
                message = message[rr:]
        else:
            for i in range(0, nnn, rr):
                SHA3.S[ 0] ^= SHA3.toLane(message, rr, ww,  0)
                SHA3.S[ 5] ^= SHA3.toLane(message, rr, ww,      ww)
                SHA3.S[10] ^= SHA3.toLane(message, rr, ww,  2 * ww)
                SHA3.S[15] ^= SHA3.toLane(message, rr, ww,  3 * ww)
                SHA3.S[20] ^= SHA3.toLane(message, rr, ww,  4 * ww)
                SHA3.S[ 1] ^= SHA3.toLane(message, rr, ww,  5 * ww)
                SHA3.S[ 6] ^= SHA3.toLane(message, rr, ww,  6 * ww)
                SHA3.S[11] ^= SHA3.toLane(message, rr, ww,  7 * ww)
                SHA3.S[16] ^= SHA3.toLane(message, rr, ww,  8 * ww)
                SHA3.S[21] ^= SHA3.toLane(message, rr, ww,  9 * ww)
                SHA3.S[ 2] ^= SHA3.toLane(message, rr, ww, 10 * ww)
                SHA3.S[ 7] ^= SHA3.toLane(message, rr, ww, 11 * ww)
                SHA3.S[12] ^= SHA3.toLane(message, rr, ww, 12 * ww)
                SHA3.S[17] ^= SHA3.toLane(message, rr, ww, 13 * ww)
                SHA3.S[22] ^= SHA3.toLane(message, rr, ww, 14 * ww)
                SHA3.S[ 3] ^= SHA3.toLane(message, rr, ww, 15 * ww)
                SHA3.S[ 8] ^= SHA3.toLane(message, rr, ww, 16 * ww)
                SHA3.S[13] ^= SHA3.toLane(message, rr, ww, 17 * ww)
                SHA3.S[18] ^= SHA3.toLane(message, rr, ww, 18 * ww)
                SHA3.S[23] ^= SHA3.toLane(message, rr, ww, 19 * ww)
                SHA3.S[ 4] ^= SHA3.toLane(message, rr, ww, 20 * ww)
                SHA3.S[ 9] ^= SHA3.toLane(message, rr, ww, 21 * ww)
                SHA3.S[14] ^= SHA3.toLane(message, rr, ww, 22 * ww)
                SHA3.S[19] ^= SHA3.toLane(message, rr, ww, 23 * ww)
                SHA3.S[24] ^= SHA3.toLane(message, rr, ww, 24 * ww)
                message = message[rr:]
                SHA3.keccakF(SHA3.S)
    
    
    @staticmethod
    def digest(msg = None, msglen = None, withReturn = None):
        '''
        Absorb the last part of the message and squeeze the Keccak sponge
        
        @param   msg:bytes?       The rest of the message
        @param   msglen:int       The length of the partial message
        @param   withReturn:bool  Whether to return the hash instead of just do a quick squeeze phrase and return `None`
        @return  :bytes?          The hash sum, or `None` if `withReturn` is `False`
        '''
        if (msg is not None) and isinstance(msg, bool):
            (msg, withReturn) = (withReturn, msg)
        elif (msglen is not None) and isinstance(msglen, bool):
            (msglen, withReturn) = (withReturn, msglen)
        if msg is None:
            msg = []
        elif msglen is not None:
            msg = msg[:msglen]
        message = SHA3.pad10star1(SHA3.M + msg, SHA3.r)
        SHA3.M = None
        nnn = len(message)
        
        rr = SHA3.r >> 3
        nn = (SHA3.n + 7) >> 3
        ww = SHA3.w >> 3
        
        # Absorbing phase
        if ww == 8:
            for i in range(0, nnn, rr):
                SHA3.S[ 0] ^= SHA3.toLane64(message, rr, 0)
                SHA3.S[ 5] ^= SHA3.toLane64(message, rr, 8)
                SHA3.S[10] ^= SHA3.toLane64(message, rr, 16)
                SHA3.S[15] ^= SHA3.toLane64(message, rr, 24)
                SHA3.S[20] ^= SHA3.toLane64(message, rr, 32)
                SHA3.S[ 1] ^= SHA3.toLane64(message, rr, 40)
                SHA3.S[ 6] ^= SHA3.toLane64(message, rr, 48)
                SHA3.S[11] ^= SHA3.toLane64(message, rr, 56)
                SHA3.S[16] ^= SHA3.toLane64(message, rr, 64)
                SHA3.S[21] ^= SHA3.toLane64(message, rr, 72)
                SHA3.S[ 2] ^= SHA3.toLane64(message, rr, 80)
                SHA3.S[ 7] ^= SHA3.toLane64(message, rr, 88)
                SHA3.S[12] ^= SHA3.toLane64(message, rr, 96)
                SHA3.S[17] ^= SHA3.toLane64(message, rr, 104)
                SHA3.S[22] ^= SHA3.toLane64(message, rr, 112)
                SHA3.S[ 3] ^= SHA3.toLane64(message, rr, 120)
                SHA3.S[ 8] ^= SHA3.toLane64(message, rr, 128)
                SHA3.S[13] ^= SHA3.toLane64(message, rr, 136)
                SHA3.S[18] ^= SHA3.toLane64(message, rr, 144)
                SHA3.S[23] ^= SHA3.toLane64(message, rr, 152)
                SHA3.S[ 4] ^= SHA3.toLane64(message, rr, 160)
                SHA3.S[ 9] ^= SHA3.toLane64(message, rr, 168)
                SHA3.S[14] ^= SHA3.toLane64(message, rr, 176)
                SHA3.S[19] ^= SHA3.toLane64(message, rr, 184)
                SHA3.S[24] ^= SHA3.toLane64(message, rr, 192)
                SHA3.keccakF(SHA3.S)
                message = message[rr:]
        else:
            for i in range(0, nnn, rr):
                SHA3.S[ 0] ^= SHA3.toLane(message, rr, ww,  0)
                SHA3.S[ 5] ^= SHA3.toLane(message, rr, ww,      ww)
                SHA3.S[10] ^= SHA3.toLane(message, rr, ww,  2 * ww)
                SHA3.S[15] ^= SHA3.toLane(message, rr, ww,  3 * ww)
                SHA3.S[20] ^= SHA3.toLane(message, rr, ww,  4 * ww)
                SHA3.S[ 1] ^= SHA3.toLane(message, rr, ww,  5 * ww)
                SHA3.S[ 6] ^= SHA3.toLane(message, rr, ww,  6 * ww)
                SHA3.S[11] ^= SHA3.toLane(message, rr, ww,  7 * ww)
                SHA3.S[16] ^= SHA3.toLane(message, rr, ww,  8 * ww)
                SHA3.S[21] ^= SHA3.toLane(message, rr, ww,  9 * ww)
                SHA3.S[ 2] ^= SHA3.toLane(message, rr, ww, 10 * ww)
                SHA3.S[ 7] ^= SHA3.toLane(message, rr, ww, 11 * ww)
                SHA3.S[12] ^= SHA3.toLane(message, rr, ww, 12 * ww)
                SHA3.S[17] ^= SHA3.toLane(message, rr, ww, 13 * ww)
                SHA3.S[22] ^= SHA3.toLane(message, rr, ww, 14 * ww)
                SHA3.S[ 3] ^= SHA3.toLane(message, rr, ww, 15 * ww)
                SHA3.S[ 8] ^= SHA3.toLane(message, rr, ww, 16 * ww)
                SHA3.S[13] ^= SHA3.toLane(message, rr, ww, 17 * ww)
                SHA3.S[18] ^= SHA3.toLane(message, rr, ww, 18 * ww)
                SHA3.S[23] ^= SHA3.toLane(message, rr, ww, 19 * ww)
                SHA3.S[ 4] ^= SHA3.toLane(message, rr, ww, 20 * ww)
                SHA3.S[ 9] ^= SHA3.toLane(message, rr, ww, 21 * ww)
                SHA3.S[14] ^= SHA3.toLane(message, rr, ww, 22 * ww)
                SHA3.S[19] ^= SHA3.toLane(message, rr, ww, 23 * ww)
                SHA3.S[24] ^= SHA3.toLane(message, rr, ww, 24 * ww)
                message = message[rr:]
                SHA3.keccakF(SHA3.S)
        
        # Squeezing phase
        if withReturn:
            rc = [0] * ((SHA3.n + 7) >> 3)
            ptr = 0
            
            olen = SHA3.n
            j = 0
            ni = min(25, rr)
            while olen > 0:
                i = 0
                while (i < ni) and (j < nn):
                    v = SHA3.S[(i % 5) * 5 + i // 5]
                    for _ in range(ww):
                        if j < nn:
                            rc[ptr] = v & 255
                            ptr += 1
                        v >>= 8
                        j += 1
                    i += 1
                olen -= SHA3.r
                if olen > 0:
                    SHA3.keccakF(SHA3.S)
            if (SHA3.n & 7) != 0:
                rc[len(rc) - 1] &= (1 << (SHA3.n & 7)) - 1
            
            return rc
        
        olen = SHA3.n
        while olen > SHA3.r:
            olen -= SHA3.r
            SHA3.keccakF(SHA3.S)
        return None
    
    
    def simpleSqueeze(times = 1):
        '''
        Force some rounds of Keccak-f
        
        @param  times:int  The number of rounds
        '''
        for i in range(times):
            SHA3.keccakF(SHA3.S)
    
    
    def fastSqueeze(times = 1):
        '''
        Squeeze as much as is needed to get a digest a number of times
        
        @param  times:int  The number of digests
        '''
        for i in range(times):
            SHA3.keccakF(SHA3.S) # Last squeeze did not do a ending squeeze
            olen = SHA3.n
            while olen > SHA3.r:
                olen -= SHA3.r
                SHA3.keccakF(SHA3.S)
    
    
    def squeeze():
        '''
        Squeeze out another digest
        
        @return  :bytes  The hash sum
        '''
        SHA3.keccakF(SHA3.S) # Last squeeze did not do a ending squeeze
        
        nn = (SHA3.n + 7) >> 3
        ww = SHA3.w >> 3
        rc = [0] * nn
        olen = SHA3.n
        j = 0
        ptr = 0
        ni = min(25, SHA3.r >> 3)
        
        while olen > 0:
            i = 0
            while (i < ni) and (j < nn):
                v = SHA3.S[(i % 5) * 5 + i // 5]
                for _ in range(ww):
                    if j < nn:
                        rc[ptr] = v
                        ptr += 1
                    v >>= 8
                    j += 1
                i += 1
            olen -= SHA3.r
            if olen > 0:
                SHA3.keccakF(SHA3.S)
        
        if (SHA3.n & 7) != 0:
            rc[len(rc) - 1] &= (1 << (SHA3.n & 7)) - 1
        
        return rc
        


if __name__ == '__main__':
    cmd = sys.argv[0]
    args = sys.argv[1:]
    if '/' in cmd:
        cmd = cmd[cmd.rfind('/') + 1:]
    if cmd.endswith('.py'):
        cmd = cmd[:-3]
    
    (O, S, R, C, W, I, J) = (None, None, None, None, None, None, None)
    (o, s, r, c, w, i, j) = (0, 0, 0, 0, 0, 0, 0)
    _o = 512             # --outputsize
    if   cmd == 'sha3-224sum':  _o = 224
    elif cmd == 'sha3-256sum':  _o = 256
    elif cmd == 'sha3-384sum':  _o = 384
    elif cmd == 'sha3-512sum':  _o = 512
    _s = 1600            # --statesize
    _c = _s - (_o << 1)  # --capacity
    _r = _s - _c         # --bitrate
    _w = _s / 25         # --wordsize
    _i = 1               # --iterations
    _j = 1               # --squeezes
    (binary, hex, multi) = (False, False, 0)
    
    files = []
    dashed = False
    linger = None
    
    for arg in args + [None]:
        if linger is not None:
            if linger[0] in ('-h', '--help'):
                sys.stderr.buffer.write(('''
SHA-3/Keccak checksum calculator

USAGE:  sha3sum [option...] < file
        sha3sum [option...] file...


OPTIONS:
        -r BITRATE
        --bitrate       The bitrate to use for SHA-3.           (default: %d)
        
        -c CAPACITY
        --capacity      The capacity to use for SHA-3.          (default: %d)
        
        -w WORDSIZE
        --wordsize      The word size to use for SHA-3.         (default: %d)
        
        -o OUTPUTSIZE
        --outputsize    The output size to use for SHA-3.       (default: %d)
        
        -s STATESIZE
        --statesize     The state size to use for SHA-3.        (default: %d)
        
        -i ITERATIONS
        --iterations    The number of hash iterations to run.   (default: %d)
        
        -j SQUEEZES
        --squeezes      The number of hash squeezes to run.     (default: %d)
        
        -h
        --hex           Read the input in hexadecimal, rather than binary.
        
        -b
        --binary        Print the checksum in binary, rather than hexadecimal.
        
        -m
        --multi         Print the chechsum at all iterations.


COPYRIGHT:

Copyright © 2013  Mattias Andrée (maandree@member.fsf.org)

This program is free software: you can redistribute it and/or modify
it under the terms of the GNU Affero General Public License as published by
the Free Software Foundation, either version 3 of the License, or
(at your option) any later version.

This program is distributed in the hope that it will be useful,
but WITHOUT ANY WARRANTY; without even the implied warranty of
MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
GNU Affero General Public License for more details.

You should have received a copy of the GNU Affero General Public License
along with this program.  If not, see <http://www.gnu.org/licenses/>.

''' % (_r, _c, _w, _o, _s, _i, _j)).encode('utf-8'))
                sys.stderr.buffer.flush()
                exit(0)
            else:
                if linger[1] is None:
                    linger[1] = arg
                    arg = None
                if linger[0] in ('-r', '--bitrate'):
                    R = int(linger[1])
                elif linger[0] in ('-c', '--capacity'):
                    C = int(linger[1])
                elif linger[0] in ('-w', '--wordsize'):
                    W = int(linger[1])
                elif linger[0] in ('-o', '--outputsize'):
                    O = int(linger[1])
                elif linger[0] in ('-s', '--statesize'):
                    S = int(linger[1])
                elif linger[0] in ('-i', '--iterations'):
                    I = int(linger[1])
                elif linger[0] in ('-j', '--squeezes'):
                    J = int(linger[1])
                else:
                    printerr(sys.argv[0] + ': unrecognised option: ' + linger[0])
                    sys.exit(1)
            linger = None
            if arg is None:
                continue
        if arg is None:
            continue
        if dashed:
            files.append(None if arg == '-' else arg)
        elif arg == '--':
            dashed = True
        elif arg == '-':
            files.append(None)
        elif arg.startswith('--'):
            if '=' in arg:
                linger = (arg[:arg.find('=')], arg[arg.find('=') + 1:])
            else:
                if arg == '--binary':
                    binary = True
                elif arg == '--multi':
                    multi += 1
                elif arg == '--hex':
                    hex = True
                else:
                    linger = [arg, None]
        elif arg.startswith('-'):
            arg = arg[1:]
            if arg[0] == 'b':
                binary = True
                arg = arg[1:]
            elif arg[0] == 'b':
                multi += 1
                arg = arg[1:]
            elif arg[0] == 'h':
                hex = True
                arg = arg[1:]
            elif len(arg) == 1:
                linger = ['-' + arg, None]
            else:
                linger = ['-' + arg[0], arg[1:]]
        else:
            files.append(arg)
    
    
    i = _i if I is None else I
    j = _j if J is None else J
    
    
    if S is not None:
        s = S
        if ((s <= 0) or (s > 1600) or (s % 25 != 0)):
            printerr(cmd + ': the state size must be a positive multiple of 25 and is limited to 1600.')
            sys.exit(6)
    
    if W is not None:
        w = W
        if (w <= 0) or (w > 64):
            printerr(cmd + ': the word size must be positive and is limited to 64.')
            sys.exit(6)
        if (S is not None) and (s != w * 25):
            printerr(cmd + ': the state size must be 25 times of the word size.')
            sys.exit(6)
        elif S is None:
            S = w * 25
    
    if C is not None:
        c = C
        if (c <= 0) or ((c & 7) != 0):
            printerr(cmd + ': the capacity must be a positive multiple of 8.')
            sys.exit(6)
    
    if R is not None:
        r = R
        if (r <= 0) or ((r & 7) != 0):
            printerr(cmd + ': the bitrate must be a positive multiple of 8.')
            sys.exit(6)
    
    if O is not None:
        o = O
        if o <= 0:
            printerr(cmd + ': the output size must be positive.')
            sys.exit(6)
    
    
    if (R is None) and (C is None) and (O is None): ## s?
        s = _s if S is None else s
        o = (((s << 5) // 100 + 7) >> 3) << 3
        r = o << 1
        c = s - r
        o = 8 if o < 8 else o
    elif (R is None) and (C is None): ## !o s?
        r = _r
        c = _c
        s = (r + c) if S is None else s
    elif R is None: ## !c o? s?
        s = _s if S is None else s
        r = s - c
        o = (8 if c == 8 else (c << 1)) if O is None else o
    elif C is None: ## !r o? s?
        s = _s if S is None else s
        c = s - r
        o = (8 if c == 8 else (c << 1)) if O is None else o
    else: ## !r !c o? s?
        s = (r + c) if S is None else s
        o = (8 if c == 8 else (c << 1)) if O is None else o
    
    
    printerr('Bitrate: %d' % r)
    printerr('Capacity: %d' % c)
    printerr('Word size: %d' % w)
    printerr('State size: %d' % s)
    printerr('Output size: %d' % o)
    printerr('Iterations: %d' % i)
    printerr('Squeezes: %d' % j)
    
    
    if r > s:
        printerr(cmd + ': the bitrate must not be higher than the state size.')
        sys.exit(6)
    if c > s:
        printerr(cmd + ': the capacity must not be higher than the state size.')
        sys.exit(6)
    if r + c != s:
        printerr(cmd + ': the sum of the bitrate and the capacity must equal the state size.')
        sys.exit(6)
    
    
    if len(files) == 0:
        files.append(None)
    if i < 1:
        printerr(cmd + ': sorry, I will only do at least one hash iteration!\n')
        sys.exit(3)
    if j < 1:
        printerr(cmd + ': sorry, I will only do at least one squeeze iteration!\n')
        sys.exit(3)
    stdin = None
    fail = False
    for filename in files:
        rc = ''
        fn = '/dev/stdin' if filename is None else filename
        with open(fn, 'rb') as file:
            try:
                if (filename is not None) or (stdin is None):
                    SHA3.initialise(r, c, o)
                    blksize = 4096
                    try:
                        blksize = os.stat(os.path.realpath(fn)).st_blksize
                        if blksize <= 0:
                            blksize = 4096
                    except:
                        pass
                    while True:
                        chunk = [ord(b) for b in file.read(blksize)]
                        if len(chunk) == 0:
                            break
                        if not hex:
                            SHA3.update(chunk)
                        else:
                            n = len(chunk) >> 1
                            for _ in range(n):
                                (a, b) = (chunk[_ << 1], chunk[(_ << 1 | 1)])
                                a = ((a & 15) + (0 if a <= '9' else 9)) << 4
                                b =  (b & 15) + (0 if b <= '9' else 0)
                                chunk[_] = a | b
                            SHA3.update(chunk, n)
                    bs = SHA3.digest(j == 1)
                    if j > 2:
                        SHA3.fastSqueeze(j - 2)
                    if j > 1:
                        bs = SHA3.squeeze();
                    if filename is None:
                        stdin = bs
                else:
                    bs = stdin
                if multi == 0:
                    for _ in range(i - 1):
                        SHA3.initialise(r, c, o)
                        bs = SHA3.digest(bs, j == 1)
                        if j > 2:
                            SHA3.fastSqueeze(j - 2)
                        if j > 1:
                            bs = SHA3.squeeze();
                    if binary:
                        write(bs)
                    else:
                        for b in bs:
                            rc += "0123456789ABCDEF"[b >> 4]
                            rc += "0123456789ABCDEF"[b & 15]
                        rc += ' ' + ('-' if filename is None else filename) + '\n'
                        write(rc.encode('utf-8'))
                elif multi == 1:
                    if binary:
                        write(bs)
                    else:
                        for b in bs:
                            rc += "0123456789ABCDEF"[b >> 4]
                            rc += "0123456789ABCDEF"[b & 15]
                        rc += '\n'
                        write(rc.encode('UTF-8'))
                    for _ in range(i - 1):
                        SHA3.initialise(r, c, o)
                        bs = SHA3.digest(bs, j == 1)
                        if j > 2:
                            SHA3.fastSqueeze(j - 2)
                        if j > 1:
                            bs = SHA3.squeeze();
                        if binary:
                            write(bs);
                        else:
                            rc = ''
                            for b in bs:
                                rc += "0123456789ABCDEF"[b >> 4]
                                rc += "0123456789ABCDEF"[b & 15]
                            rc += '\n'
                            write(rc.encode('UTF-8'))
                else:
                    got = set()
                    loop = None
                    for _ in range(i):
                        if _ > 0:
                            pass
                        rc = ''
                        for b in bs:
                            rc += "0123456789ABCDEF"[b >> 4]
                            rc += "0123456789ABCDEF"[b & 15]
                        if loop is None:
                            if rc in got:
                                loop = rc
                            else:
                                got.add(rc)
                        if loop == rc:
                            rc = '\033[31m%s\033[00m' % rc;
                        write(rc.encode('utf-8'))
                        flush()
                    if loop is not None:
                        printerr('\033[01;31mLoop found\033[00m')
                flush()
            except Exception as err:
                printerr(cmd + ': connot read file: ' + fn + ': ' + str(err))
                fail = True
        flush()
    if fail:
        sys.exit(5)
