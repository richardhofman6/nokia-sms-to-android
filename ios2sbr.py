#!/usr/bin/env python
# Copyright Francis Devereux 2011
# Edits by Richard Hofman, 2018

"""Converts SMS message data from iOS DB SQLite dump to SMS Backup and
Restore for Android (by Ritesh Sahu).

Useful for transferring SMSes from iPhone backups to Android phones"""

import csv, time, sys
from datetime import datetime

from optparse import OptionParser
from xml.dom.minidom import Document

def has_alpha(strng):
    for c in strng:
        if c.isalpha():
            return True
    return False

def parse_csv_dump(csvfile):
    chats = {}
    reader = csv.reader(csvfile)
    for row in reader:
        item = {}
        item['id'] = row[0]
        item['sent'] = row[1] == '1'
        item['date'] = datetime.fromtimestamp(int(row[2][:9]) + 978307200)
        item['body'] = row[3]
        item['service'] = row[4]
        if item['id'] not in chats.keys():
            chats[item['id']] = []
        chats[item['id']].append(item)
    return chats

def write_output_csv(chats):
    with open('sms_android_import.csv', 'a') as csvfile:
        writer = csv.writer(csvfile)
        writer.writerow(['Contact', 'Body', 'Date', 'Sent/Received'])
        for contact, messages in chats.items():
            for message in messages:
                writer.writerow([contact, message['body'], message['date'], "SENT" if message['sent'] else "RECEIVED"])
        csvfile.close()

class SMS:
    def read_from_ios_csv_row(self, csv_row):
        chat = csv_row[0]
        self.valid = csv_row and len(csv_row) == 5
        if '@' in chat or has_alpha(chat) or len(chat) < 7:
            self.valid = False
        if not self.valid:
            return

        self.direction = 'sent' if csv_row[1] == '1' else 'received'
        self.other_party = csv_row[0]
        msg_datetime = datetime.fromtimestamp(int(csv_row[2][:9]) + 978307200)
        self.java_time = time.mktime(msg_datetime.timetuple()) * 1000
        self.body = csv_row[3]

    def populate_sbr_element(self, sms_el):
        sms_el.setAttribute('address', self.other_party)
        sms_el.setAttribute('date', '%d' % int(self.java_time))
        if self.direction == 'received':
            t = '1'
        else:
            t = '2'
        sms_el.setAttribute('type', t)

        sms_el.setAttribute('body', self.body)
        sms_el.setAttribute('read', str(self.read))

        sms_el.setAttribute('protocol', '0')
        sms_el.setAttribute('subject', 'null')
        sms_el.setAttribute('toa', '0')
        sms_el.setAttribute('sc_toa', '0')
        sms_el.setAttribute('service_center', 'null')
        sms_el.setAttribute('status', '-1')
        sms_el.setAttribute('locked', '0')
       
    def __str__(self):
        return 'SMS(valid=%d, direction=%s, other_party=%s, java_time=%d, read=%d, body=%s)' % \
            (self.valid, self.direction, self.other_party, self.java_time, self.read, self.body)

def main():
    usage = "usage: %prog iphone_sms_in.csv sms_backup_restore_out.xml"
    parser = OptionParser(usage=usage)

    (options, args) = parser.parse_args()

    if len(args) < 2:
        parser.print_help()
        sys.exit(1)

    ios_filename = args[0]
    sbr_filename = args[1]

    with open(ios_filename, 'r') as ios_file:
        #dialect = csv.Sniffer().sniff(ios_file.read(1024))
        ios_file.seek(0)
        csv_reader = csv.reader(ios_file)
        sbr_doc = Document()
        smses_el = sbr_doc.createElement("smses")
        sbr_doc.appendChild(smses_el)
        print("Reading and converting CSV file...")
        for csv_row in csv_reader:
            sms = SMS()
            sms.read_from_ios_csv_row(csv_row)
            sms.read = 1
            if not sms.valid:
                continue

            sms_el = sbr_doc.createElement('sms')
            sms.populate_sbr_element(sms_el)
            smses_el.appendChild(sms_el)

        print("Writing outfile file.")
        with open(sbr_filename, 'w') as sbr_file:
            sbr_file.write(sbr_doc.toprettyxml())
        print("Done.")

if __name__ == '__main__':
    main()
