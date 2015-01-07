#!/usr/bin/python

# Copyright (c) 2015 Stanford University
#
# Permission to use, copy, modify, and distribute this software for any
# purpose with or without fee is hereby granted, provided that the above
# copyright notice and this permission notice appear in all copies.
#
# THE SOFTWARE IS PROVIDED "AS IS" AND THE AUTHOR(S) DISCLAIM ALL WARRANTIES
# WITH REGARD TO THIS SOFTWARE INCLUDING ALL IMPLIED WARRANTIES OF
# MERCHANTABILITY AND FITNESS. IN NO EVENT SHALL AUTHORS BE LIABLE FOR
# ANY SPECIAL, DIRECT, INDIRECT, OR CONSEQUENTIAL DAMAGES OR ANY DAMAGES
# WHATSOEVER RESULTING FROM LOSS OF USE, DATA OR PROFITS, WHETHER IN AN
# ACTION OF CONTRACT, NEGLIGENCE OR OTHER TORTIOUS ACTION, ARISING OUT OF
# OR IN CONNECTION WITH THE USE OR PERFORMANCE OF THIS SOFTWARE.

"""
Runs a simplified simulations for the credit based transport scheme
"""
import os
import sys
import random
import numpy as np
from optparse import OptionParser

"""
@param  msg: A message that will be generated at sender and must be transmitted.
             A list of [message_id, message_size]
@type   msg: C[int, int] 

@param  pkt: A list of [message_id, message_size, priority]. Represents a packet
             from a message along with the granted priority for that packet and
             the remaining size of message that this packet blongs to.
@type   pkt: C[int, int, int]

@param  delayedPkt: Represent a packet that is taken out of txQueue and should
                    be received in rxQueue after some delay. A list of
                    [pkt, delay]
@type   delayedPkt: C[pkt, int]

@param  txQueue: The transmit queue at the input of simulation. A list of
                 messages as [msg1, msg2, ..] that are sorted by the message
                 size from smallest to largest.
@type   txQueue: C[msg, msg, msg, ...]

@param  rxQueue: Reperesent a list of pkt that are scheduled and received in the
                 output (edge) queue of the network. A list of packets as
                 [pkt1, pkt2, ...] that are sorted by the priority from highest
                 priority (smaller number) to lowest priority.
@type   rxQueue: C[pkt, pkt, pkt, ..]

@param  delayQueue: This queue contains all packets that are scheduled and has
                    left txQueue but has not yet received in rxQueue. These
                    packets are in flight and experiencing some delay in the
                    network. This is a list of [delayedPkt1, delayedPkt2, ...]
                    and this list is sorted by the delay of the packets from
                    lowest to highest.
@type   delayQueue: C[delayedPkt, delayedPkt, ...]

@param  distMatrix: A list of cumulative probabilities for different sizes. From
                    the lowes size to the highest size, for each size there is
                    a row in this matrix as
                    row=[cumulative_probability, size]. So this matrix is a
                    list of [row1, row2, ...]
@type   distMatrix: C[[float, int], [float, int], ...]

@param  pktOutTime: A dictionary from key:message_id to a value:list[pkt_info].
                    Each pkt_info is some information for one packet that
                    belongs to that message. Each pkt_info is a list of two
                    elements as pkt_info[time_slot, priority, msgSize] that is
                    the time slot at which the packet has left the rxQueue and
                    the priority that was assigned to that packet and the
                    size of the message. 
@type   pktOutTime: Dictionary{key(messge_id):value([pkt_info1, pkt_info2, ..])}

@param  msgList: A list of messages that has everh been added to txQueue
                      along with their sizes. A list[messageId, messageSize]
@type   msgList: C[int, int]
"""

def generateMsgSize(distMatrix):
    randomNumber = random.random()
    for row in distMatrix:
        if (row[0] > randomNumber):
            return row[1]


class Scheduler():
    def __init__(self, txQueue = [], rxQueue = [], delayQueue = []):
        self.txQueue = txQueue
        self.rxQueue = rxQueue
        self.delayQueue= delayQueue 

    def addPktToDelayQueue(self, pkt, avgDelay):
        msgId = pkt[0]
        msgSize = pkt[1]
        pktPrio = pkt[2]
        delay = np.random.poisson(avgDelay)
        delayedPkt = list([msgId, msgSize, pktPrio, delay])
        self.delayQueue.append(delayedPkt)
        self.delayQueue.sort(cmp=lambda x, y: cmp(x[3], y[3]))

    def depleteDelayQueue(self):
        for delayPkt in self.delayQueue[:]:
            if (delayPkt[-1] == 0):
                pkt = delayPkt[0:-1] 
                self.rxQueue.append(pkt)
                self.delayQueue.remove(delayPkt)
        self.rxQueue.sort(cmp=lambda x, y: cmp(x[2], y[2]))

        for delayPkt in self.delayQueue:
            delayPkt[-1] -= 1

    def simpleScheduler(self, slot, pktOutTime):
        prio = 0
        if (len(self.txQueue) > 0):
            highPrioMsg = self.txQueue[0]
            highPrioPkt = list([highPrioMsg[0], highPrioMsg[1], prio])
            highPrioMsg[1] -= 1
            self.addPktToDelayQueue(highPrioPkt, 4)    
            if (highPrioMsg[1] == 0):
                self.txQueue.pop(0)
                
        self.depleteDelayQueue() 
        if (len(self.rxQueue) > 0):
            pkt = self.rxQueue.pop(0)
            msgId = pkt[0]
            msgSize = pkt[1]
            pktPrio = pkt[2]
            if (msgId in pktOutTime):
                pktOutTime[msgId].append([slot, pktPrio, msgSize])
            else:
                pktOutTime[msgId] = list()
                pktOutTime[msgId].append([slot, pktPrio, msgSize])


def run(steps, rho, sizeAvg, distMatrix, msgDict, pktOutTime):
    txQueue = list()
    rxQueue = list() 
    delayQueue = list()
    scheduler = Scheduler(txQueue, rxQueue, delayQueue)
    probPerSlot = rho / sizeAvg 
    msgId = 0
    for slot in range(steps):
        if (random.random() < probPerSlot):
            newMsg = [msgId, generateMsgSize(distMatrix)]
            txQueue.append(newMsg[:]) 
            txQueue.sort(cmp=lambda x, y: cmp(x[1], y[1]))
            msgDict[msgId] = newMsg[1] 
            msgId += 1

        scheduler.simpleScheduler(slot, pktOutTime)
            
if __name__ == '__main__':
    steps = 10000
    rho = 0.8
    #distMatrix = [[0.8, 1], [0.85, 2], [0.88, 3], [0.9, 4], [0.93, 5],
    #                [0.95, 6], [0.97, 7], [0.98, 8], [0.99, 9], [1.0, 10]]
    distMatrix = [[0.6, 1], [0.65, 2], [0.7, 3], [0.75, 4], [0.8, 5], [0.84, 6],
                    [0.88, 7], [0.92, 8], [0.96, 9], [1.0, 10]]
    sizeAvg = 0
    prevProb = 0
    for row in distMatrix:
        sizeAvg += row[1] * (row[0] - prevProb)
        prevProb = row[0]                                                       

    pktOutTime = dict() 
    msgDict = dict()
    run(steps, rho, sizeAvg, distMatrix, msgDict, pktOutTime)
    for key in msgDict:
        print "msgId: {}, msgSize: {}, pkts: {}".format(key, 
                msgDict[key], pktOutTime[key] if key in pktOutTime else [])
