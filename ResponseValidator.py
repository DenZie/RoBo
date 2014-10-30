import time as tm
from datetime import datetime
import pytz
import re
from robot import libraries
import enum
import xlrd
import csv
# bi =libraries.BuiltIn.BuiltIn()

class ERRORS: 
    SIGON_INVALID = '15500'
    SIGON_COUNT_EXCEED = '15502'
    INVALID_FID = '2000'
    messages ={SIGON_INVALID: 'Signon Invalid', 
               SIGON_COUNT_EXCEED: 'Maximum invalid signon count exceeded. Please contact your financial institution for assistance.',
               INVALID_FID:'Invalid FID sent in Request'}
    
    @staticmethod
    def getMessage(ercode):
        return messages[ercode]
    
def getInnerXml(xml, tag):
    if (xml.count('<%s>' %(tag))/2) > 1:
        data = re.sub('<%s>(.*)</%s>' % (tag,tag), '', xml)
        xml = xml.replace('</%s>' %(tag), '')
        taglist = xml.split('<%s>' %(tag))
        taglist[len(taglist)-1]
        return (data,taglist[1:])
    else:
        match = re.findall('<%s>(.*)</%s>' % (tag,tag), xml)
        innerXml=''
        if(match != None):
            for column in match:
                innerXml +=column
            data = re.sub('<%s>(.*)</%s>' % (tag,tag), '', xml)
        return  (data,innerXml)

class Response:
    def __init__(self, data, fiid):
        self.data =data
        self.fiid= fiid
        
    def checkRestData(self):
        containers = ['OFX', 'SIGNONMSGSRSV1', 'SIGNUPMSGSRSV1']
        self.data = self.removeContainers(self.data, containers)
        if len(self.data)>0:
            bi.fail( 'Additional data found on the OFX response than expected.')
            
    def removeContainers(self, data, containers):
        for container in containers:
            data = data.replace('<' + container + '>', '')
            data = data.replace('</' + container + '>', '')
        return data
    
    def validateDate(self,source, tag):
        m= re.findall('(<%s>[^<]+)'%(tag), source)
#         eastern = pytz.timezone('US/Pacific')
#         u=datetime.utcnow()
#         u=u.replace(tzinfo=pytz.utc)
#         dt = datetime.astimezone(u, eastern).strftime("%Y%m%d%H")
#         return m[0].count(dt)==1
        return source.replace(m[0], '')
        
    
    def validateHeader(self):
        data=  self.data.replace('\n', '')
        pattern = 'OFXHEADER:100DATA:OFXSGMLVERSION:102SECURITY:NONEENCODING:USASCIICHARSET:1252COMPRESSION:NONEOLDFILEUID:NONENEWFILEUID:NONE'
        msg='Header in OFX response does not match expected.'
        self.data = self.checkAndRemoveData(data, pattern, msg)
            
    def checkAndRemoveData(self, source, pattern, msg):
        if source.count(pattern) != 1:
#             bi.fail(msg + ' [' +pattern + ']')
            print msg + ' [' +pattern + ']'
        else:
            return source.replace(pattern, '')
    def sonrqPass(self):
        self.data, sonrs = getInnerXml(self.data, 'SONRS')
        pattern = '<STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS>'
        msg= 'sign on response does not match the expected.'
        sonrs = self.checkAndRemoveData(sonrs, pattern, msg)
        sonrs = self.validateDate(sonrs, 'DTSERVER')
        pattern = '<LANGUAGE>ENG<FI><ORG>DI<FID>%s</FI>'%(self.fiid)
        sonrs = self.checkAndRemoveData(sonrs, pattern, msg)
        if len(sonrs)>0:
            bi.fail('Additional data found on the SONRQ response than expected.')

    def sonrqFailed(self, ercode): 
        self.data, sonrs = getInnerXml(self.data, 'SONRS')
        pattern = '<STATUS><CODE>%s<SEVERITY>ERROR<MESSAGE>%s</STATUS>'%(ercode, ERRORS.messages[ercode])
        msg= 'sign on response does not match the expected.'
        sonrs = self.checkAndRemoveData(sonrs, pattern, msg)
        sonrs = self.validateDate(sonrs, 'DTSERVER')
        pattern = '<LANGUAGE>ENG<FI><ORG>DI<FID>%s</FI>'%(self.fiid)
        sonrs = self.checkAndRemoveData(sonrs, pattern, msg)
        if len(sonrs)>0:
            bi.fail('Additional data found on the SONRQ response than expected.')
        
    def pinchtrnrsPass(self, uid):
        self.sonrqPass()
        self.data, pinchtrnrs = getInnerXml(self.data, 'PINCHTRNRS')
        pattern = '<TRNUID>TRAN_UID_PINCHRQ_0002<STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS><PINCHRS><USERID>%s</PINCHRS>'%(uid)
        msg= 'Pin change response does not match the expected.'
        pinchtrnrs = self.checkAndRemoveData(pinchtrnrs, pattern, msg)
        if len(pinchtrnrs)>0:
            bi.fail('Additional data found on the SONRQ response than expected.')
        

    def pinchtrnrsFail(self, uid, ercode):
        pattern = '<TRNUID>TRAN_UID_PINCHRQ_0002<STATUS><CODE>%s<SEVERITY>ERROR<MESSAGE>%s</STATUS>'%(ercode, ERRORS.messages[ercode])
        if ercode == ERRORS.SIGON_INVALID or ercode == ERRORS.SIGON_COUNT_EXCEED:
            self.sonrqFailed(ercode)
            pattern = '<TRNUID>TRAN_UID_PINCHRQ_0002<STATUS><CODE>%s<SEVERITY>ERROR<MESSAGE>%s</STATUS><PINCHRS><USERID>%s</PINCHRS>'%(ercode, ERRORS.messages[ercode], uid)
        else:
            self.sonrqPass()
        self.data, pinchtrnrs = getInnerXml(self.data, 'PINCHTRNRS')
        msg = 'pin change response does not match the expected.'
        pinchtrnrs = self.checkAndRemoveData(pinchtrnrs, pattern, msg)
        if len(pinchtrnrs)>0:
            bi.fail('Additional data found on the SONRQ response than expected.')
            
    def acctinforsPass(self, acctinfolstact):
        self.sonrqPass()
        self.data, acctinfotrnrs = getInnerXml(self.data, 'ACCTINFOTRNRS')
        pattern = '<TRNUID>TRAN_UID_ACCTINFORQ_0001b<STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS>'
        msg= 'account info response does not match the expected.'
        acctinfotrnrs = self.checkAndRemoveData(acctinfotrnrs, pattern, msg)
        acctinfotrnrs, acctinfors = getInnerXml(acctinfotrnrs, 'ACCTINFORS')
        acctinfors = self.validateDate(acctinfors, 'DTACCTUP')
        for ed in acctinfolstact:
            pattern='<ACCTINFO><DESC>%s<BANKACCTINFO><BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM><SUPTXDL>%s<XFERSRC>%s<XFERDEST>%s<SVCSTATUS>%s</BANKACCTINFO></ACCTINFO>' %(ed['DESC'],  ed['BANKID'], ed['ACCTID'], ed['ACCTTYPE'], ed['SUPTXDL'], ed['XFERSRC'], ed['XFERDEST'], ed['SVCSTATUS'])
            acctinfors = self.checkAndRemoveData(acctinfors, pattern, msg)
        if len(acctinfotrnrs + acctinfors)>0:
            bi.fail('Additional data found on the SONRQ response than expected.')
        return pattern

    def acctinfotrnrsFail(self, ercode):
        if ercode == ERRORS.SIGON_INVALID:
            self.sonrqFailed(ercode)
        else:
            self.sonrqPass()
        self.data, acctinfotrnrs = getInnerXml(self.data, 'ACCTINFOTRNRS')
        pattern = '<TRNUID>TRAN_UID_ACCTINFORQ_0001a<STATUS><CODE>%s<SEVERITY>ERROR<MESSAGE>%s</STATUS>'%(ercode, ERRORS.messages[ercode])
        msg= 'account info response does not match the expected.'
        acctinfotrnrs = self.checkAndRemoveData(acctinfotrnrs, pattern, msg)
        if len(acctinfotrnrs)>0:
            bi.fail('Additional data found on the SONRQ response than expected.')
            
    def proftrnrqPass(self, url, spname):
        self.sonrqPass()
        self.data, proftrnrs = getInnerXml(self.data, 'PROFTRNRS')
        pattern = '<TRNUID>TRAN_UID_OFX_PROFRQ_FT_1<STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS>'
        msg= 'account info response does not match the expected.'
        proftrnrs = self.checkAndRemoveData(proftrnrs, pattern, msg)
        proftrnrs , profrs = getInnerXml(proftrnrs, 'PROFRS')
        profrs , msgsetlist = getInnerXml(proftrnrs, 'MSGSETLIST')
        msgsetlist, signonmsgset = getInnerXml(msgsetlist, 'SIGNONMSGSET')
        self.signonmsgset(signonmsgset, url, spname)
        msgsetlist, signupmsgset = getInnerXml(msgsetlist, 'SIGNUPMSGSET')
        self.signupmsgset(signupmsgset, url, spname)
        msgsetlist, bankmsgset = getInnerXml(msgsetlist, 'BANKMSGSET')
        self.bankmsgset(signupmsgset, url, spname)
        msgsetlist, billpaymsgset = getInnerXml(msgsetlist, 'BILLPAYMSGSET')
        self.billpaymsgset(signupmsgset, url, spname)
        msgsetlist, profmsgset = getInnerXml(msgsetlist, 'PROFMSGSET')
        self.profmsgset(signupmsgset, url, spname)
        pattern = '<SIGNONINFOLIST><SIGNONINFO><SIGNONREALM>default<MIN>4<MAX>8<CHARTYPE>ALPHAORNUMERIC<CASESEN>Y<SPECIAL>N<SPACES>N<PINCH>Y<CHGPINFIRST>N</SIGNONINFO></SIGNONINFOLIST>'
        profrs = self.checkAndRemoveData(profrs, pattern, msg)
        profrs = self.validateDate(profrs, 'DTPROFUP')
        pattern = '<FINAME>Candidate 8<ADDR1>123 Street<CITY>Calabasas<STATE>CA<POSTALCODE>90210<COUNTRY>US<CSPHONE>1-800-123-4567<TSPHONE>1-800-234-6789<FAXPHONE>1-800-888-7777<URL>https://www.candidate8.com<EMAIL>David.Schwab@DigitalInsight.com<INTU.BROKERID>DI<INTU.RTN>999999999'
        profrs = self.checkAndRemoveData(profrs, pattern, msg)
#       TODO  update the above 2 pattern matching based on the required data.
        if len(proftrnrs+profrs+msgsetlist)>0:
            bi.fail('Additional data found on the SONRQ response than expected.')
                        
    def signonmsgset(self, data, url,spname):
        data = self.removeContainers(data, ['SIGNONMSGSETV1'])
        data = self.msgsetcore(data, url, spname)
        if len(data)>0: 
            bi.fail('Additional data found on the tag SIGNONMSGSETV1 for PROFTRNRQ response than expected.')
            
    def msgsetcore(self, msgsetcoredata, url, spname):
        pattern  = '<MSGSETCORE><VER>1<URL>%s<OFXSEC>NONE<TRANSPSEC>N<SIGNONREALM>default<LANGUAGE>ENG<SYNCMODE>LITE<RESPFILEER>Y<SPNAME>%s</MSGSETCORE>' % (url, spname)
        msg = 'profile request response data under the tag [SIGNONMSGSETV1] does not match the expected.'
        data = self.checkAndRemoveData(data, pattern, msg)
        return msgsetcoredata
    
    def signupmsgset(self, data, url,spname):
        data = self.removeContainers(data, ['SIGNUPMSGSETV1'])
        data = self.msgsetcore(data, url, spname)
        pattern = '<WEBENROLL><URL>N</WEBENROLL><CHGUSERINFO>N<AVAILACCTS>Y<CLIENTACTREQ>N'
        msg = 'profile request response data under the tag [SIGNUPMSGSETV1] does not match the expected.'
        if len(data)>0: 
            bi.fail('Additional data found on the tag SIGNUPMSGSETV1 for PROFTRNRQ response than expected.')
          
    def bankmsgset(self, data, url,spname):
        data = self.removeContainers(data, ['BANKMSGSETV1'])
        data = self.msgsetcore(data, url, spname)
        pattern = '<CLOSINGAVAIL>Y<XFERPROF><PROCENDTM>170000<CANSCHED>N<CANRECUR>N<CANMODXFERS>N<CANMODMDLS>N<MODELWND>0<DAYSWITH>0<DFLTDAYSTOPAY>0</XFERPROF><EMAILPROF><CANEMAIL>N<CANNOTIFY>N</EMAILPROF>'
        msg = 'profile request response data under the tag [BANKMSGSETV1] does not match the expected.'
        if len(data)>0: 
            bi.fail('Additional data found on the tag BANKMSGSETV1 for PROFTRNRQ response than expected.')

    def billpaymsgset(self, data, url,spname):
        data = self.removeContainers(data, ['BILLPAYMSGSETV1'])
        data = self.msgsetcore(data, url, spname)
        pattern = '<DAYSWITH>0<DFLTDAYSTOPAY>4<XFERDAYSWITH>0<XFERDFLTDAYSTOPAY>0<PROCDAYSOFF>SATURDAY<PROCDAYSOFF>SUNDAY<PROCENDTM>235959[-5:EST]<MODELWND>30<POSTPROCWND>180<STSVIAMODS>N<PMTBYADDR>Y<PMTBYXFER>N<PMTBYPAYEEID>N<CANADDPAYEE>Y<HASEXTDPMT>N<CANMODPMTS>Y<CANMODMDLS>N<DIFFFIRSTPMT>N<DIFFLASTPMT>N'
        msg = 'profile request response data under the tag [BILLPAYMSGSETV1] does not match the expected.'
        if len(data)>0: 
            bi.fail('Additional data found on the tag BILLPAYMSGSETV1 for PROFTRNRQ response than expected.')
                      
    def profmsgset(self, data, url,spname):
        data = self.removeContainers(data, ['PROFMSGSETV1'])
        data = self.msgsetcore(data, url, spname)
        if len(data)>0: 
            bi.fail('Additional data found on the tag PROFMSGSETV1 for PROFTRNRQ response than expected.')                      
                                
def check_acctinforq_req_succeeded(res, acctinfolst):
    rs = Response(res, acctinfolst[0]['FID'])
    rs.validateHeader()
    return rs.acctinforsPass(acctinfolst)
    rs.checkRestData()    
               
def check_sonrq_req_failed(data, fiid, ercode):
    rs = Response(data, fiid)
    rs.validateHeader()
    rs.sonrqFailed(ercode)
    rs.checkRestData()
                 
def check_sonrq_req_succeeded(data,fiid):
    rs = Response(data, fiid)
    header=  rs.validateHeader()
    rs.sonrqPass()
    rs.checkRestData()
    
def check_pinchrq_req_succeeded(data, fiid, uid):
    rs = Response(data, fiid)
    rs.validateHeader()
    rs.pinchtrnrsPass(uid)
    rs.checkRestData()
    
def check_pinchrq_req_failed(data, fiid, uid, ercode):
    rs = Response(data, fiid)
    rs.validateHeader()
    rs.pinchtrnrsFail(uid, ercode)
    rs.checkRestData()
    


def check_acctinforq_req_failed(data, fiid, ercode):
    rs = Response(data, fiid)
#     rs.validateHeader()
    rs.acctinfotrnrsFail(ercode)
    rs.checkRestData()     
        
  

def validate_OFX_response(apiName, params):
    rs = Response(data, fiid)
    validator = getattr(rs, apiName)
    validator(params)
    rs.validateHeader()
#     rs.proftrnrqPass(ercode, url, spname)
    rs.checkRestData()     

acct_info_pass ='<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS><DTSERVER>20141015045018.565[-7:PDT]<LANGUAGE>ENG<FI><ORG>DI<FID>9504</FI></SONRS></SIGNONMSGSRSV1><SIGNUPMSGSRSV1><ACCTINFOTRNRS><TRNUID>TRAN_UID_ACCTINFORQ_0001a<STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS><ACCTINFORS><DTACCTUP>20141015045031.095[-7:PDT]</ACCTINFORS></ACCTINFOTRNRS></SIGNUPMSGSRSV1></OFX>'
acct_info_pass2 ='<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS><DTSERVER>20131119101321.955[-8:PST]<LANGUAGE>ENG<FI><ORG>DI<FID>0506</FI></SONRS></SIGNONMSGSRSV1><SIGNUPMSGSRSV1><ACCTINFOTRNRS><TRNUID>TRAN_UID_ACCTINFORQ_0001b<STATUS><CODE>0<SEVERITY>INFO<MESSAGE>SUCCESS</STATUS><ACCTINFORS><DTACCTUP>20131119101413.782[-8:PST]<ACCTINFO><DESC>Primary Checking or Share Draft<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>7777777333<ACCTTYPE>CHECKING</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Credit Line Loan<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>9900000026<ACCTTYPE>CREDITLINE</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Installment Loan<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>9900000028<ACCTTYPE>CREDITLINE</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Money Market Account<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>9900000022<ACCTTYPE>MONEYMRKT</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Certificate of Deposit Account<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>9900000025<ACCTTYPE>SAVINGS</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>User Defined Savings Account<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>9900000040<ACCTTYPE>SAVINGS</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Savings or Share Account<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>972628729<ACCTTYPE>SAVINGS</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Time Deposit (Depricated)<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>9900000045<ACCTTYPE>SAVINGS</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Mortgage Loan<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>9900000031<ACCTTYPE>CREDITLINE</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Checking - CONTROL - TRANSFERS ALLOWED<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>387392729471<ACCTTYPE>CHECKING</BANKACCTFROM><SUPTXDL>Y<XFERSRC>Y<XFERDEST>Y<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>User Defined Credit Line<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>9900000393<ACCTTYPE>CREDITLINE</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO><ACCTINFO><DESC>Secondary Checking or Share Draft<BANKACCTINFO><BANKACCTFROM><BANKID>114900685<ACCTID>928279282<ACCTTYPE>CHECKING</BANKACCTFROM><SUPTXDL>Y<XFERSRC>N<XFERDEST>N<SVCSTATUS>ACTIVE</BANKACCTINFO></ACCTINFO></ACCTINFORS></ACCTINFOTRNRS></SIGNUPMSGSRSV1></OFX>'

# acct_info_fail1 ='<OFX><SIGNONMSGSRSV1><SONRS><STATUS><CODE>15500<SEVERITY>ERROR<MESSAGE>Signon Invalid</STATUS><DTSERVER>20141015051006.853[-8:PST]<LANGUAGE>ENG<FI><ORG>DI<FID>0507</FI></SONRS></SIGNONMSGSRSV1><SIGNUPMSGSRSV1><ACCTINFOTRNRS><TRNUID>TRAN_UID_ACCTINFORQ_0001a<STATUS><CODE>15500<SEVERITY>ERROR<MESSAGE>Signon Invalid</STATUS></ACCTINFOTRNRS></SIGNUPMSGSRSV1></OFX>'
# 
accountinfo = [{'DESC':'Primary Checking or Share Draft', 'BANKID':'114900685','ACCTID':'7777777333','ACCTTYPE':'CHECKING','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Credit Line Loan', 'BANKID':'114900685','ACCTID':'9900000026','ACCTTYPE':'CREDITLINE','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Installment Loan', 'BANKID':'114900685','ACCTID':'9900000028','ACCTTYPE':'CREDITLINE','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Money Market Account', 'BANKID':'114900685','ACCTID':'9900000022','ACCTTYPE':'MONEYMRKT','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Certificate of Deposit Account', 'BANKID':'114900685','ACCTID':'9900000025','ACCTTYPE':'SAVINGS','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'User Defined Savings Account', 'BANKID':'114900685','ACCTID':'9900000040','ACCTTYPE':'SAVINGS','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Savings or Share Account', 'BANKID':'114900685','ACCTID':'972628729','ACCTTYPE':'SAVINGS','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Time Deposit (Depricated)', 'BANKID':'114900685','ACCTID':'9900000045','ACCTTYPE':'SAVINGS','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Mortgage Loan', 'BANKID':'114900685','ACCTID':'9900000031','ACCTTYPE':'CREDITLINE','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Checking - CONTROL - TRANSFERS ALLOWED', 'BANKID':'114900685','ACCTID':'387392729471','ACCTTYPE':'CHECKING','SUPTXDL':'Y','XFERSRC':'Y','XFERDEST':'Y','SVCSTATUS':'ACTIVE'},
               {'DESC':'User Defined Credit Line', 'BANKID':'114900685','ACCTID':'9900000393','ACCTTYPE':'CREDITLINE','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'},
               {'DESC':'Secondary Checking or Share Draft', 'BANKID':'114900685','ACCTID':'928279282','ACCTTYPE':'CHECKING','SUPTXDL':'Y','XFERSRC':'N','XFERDEST':'N','SVCSTATUS':'ACTIVE'}]

# check_acctinforq_req_succeeded(acct_info_pass2, '0506', accountinfo)
