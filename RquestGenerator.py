import time
import xlrd
import csv
from robot.libraries.BuiltIn import BuiltIn

class dataReader:
    def __init__(self, fileName, sheetName):
        global worksheet
        workbook = xlrd.open_workbook(fileName)
        sheets= workbook.sheet_names()
        worksheet = workbook.sheet_by_index(0)
        heads =[]
        data =[]
        if sheetName in sheets:
            worksheet = workbook.sheet_by_name(sheetName)
        for i in range(0, worksheet.ncols):
            heads.append(worksheet.cell_value(0,i))
    def readData(self, startIndex=1, stopIndex=-1):
        global data
        headers =[]
        for c in range(1, worksheet.ncols):
            headers.append(worksheet.cell_value(0,c))
        data ={}
        if  stopIndex == -1:
            stopIndex=worksheet.nrows
        dataId = worksheet.cell_value(startIndex,0)   
        row= []
#         row.append(headers)
        for r in range(startIndex, stopIndex):
            column = {}
            for c in range(1, worksheet.ncols):
                column[headers[c-1]]=worksheet.cell_value(r,c)
#             if r+1 != stopIndex:
            NxtdataId= worksheet.cell_value(r,0)                
            if dataId != NxtdataId:
                self.setVariable(dataId, row)
                data[dataId]=row
                row =[]
#                 row.append(headers) 
            row.append(column)
            dataId = NxtdataId
        data[NxtdataId]=row
        self.setVariable(NxtdataId, row)

    def setVariable(self,name, value):
        BuiltIn().set_global_variable('${%s}' %(name), value)
        
class Requests:
    def acctinforq(self, params):
        return '<ACCTINFOTRNRQ><TRNUID>TRAN_UID_ACCTINFORQ_0001a<ACCTINFORQ><DTACCTUP>19700101</ACCTINFORQ></ACCTINFOTRNRQ>'

    def intrarq(self, params):
        frBankDetail = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['FRBANKID'], params['FRACCTID'], params['FRACCTTYPE'])
        toBankDetail = 'BANKACCTTO><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTTO>' %(params['TOBANKID'], params['TOACCTID'], params['TOACCTID'])
        return '<INTRATRNRQ><TRNUID>TRANUID_INTRARQ_2<INTRARQ><XFERINFO>%s<%s<TRNAMT>%s<DTDUE>%s</XFERINFO></INTRARQ></INTRATRNRQ>' %(frBankDetail, toBankDetail, params['TRNAMT'], params['DTDUE'])
#     
    def intrasyncrq(self, params):
        frBankDetail = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['FRBANKID'], params['FRACCTID'], params['FRACCTTYPE'])
        return '<INTRASYNCRQ><REFRESH>Y<REJECTIFMISSING>N%s</INTRASYNCRQ>' %(frBankDetail)
 
    def payeedelrq(self, params):
        return '<PAYEETRNRQ><TRNUID>BP_DELETEPAYEE_1<PAYEEDELRQ><PAYEELSTID>%s</PAYEEDELRQ></PAYEETRNRQ>' %(params['payeelstid'])
 
    def payeemodrq(self, params):
        addressTag = self.generateAddressData(params['address'])
        return '<PAYEETRNRQ><TRNUID>BP_MODPAYEE_1<PAYEEMODRQ><PAYEELSTID>%s<PAYEE>%s</PAYEE><PAYACCT>883733</PAYEEMODRQ></PAYEETRNRQ>' %(params['payeelstid'], addressTag)
 
    def payeerq(self,  params):
        addressTag = self.generateAddressData(params['address'])
        return '<PAYEETRNRQ><TRNUID>BP_ADDPAYEE_1<PAYEERQ><PAYEE>%s</PAYEE><PAYACCT>%s</PAYEERQ></PAYEETRNRQ>' %(addressTag, params['payacct'])
 
    def payeesyncrq(self, params):
        return '<PAYEESYNCRQ><REFRESH>Y<REJECTIFMISSING>N</PAYEESYNCRQ>'
# 
    def pinchrq(self, params):
        return '<PINCHTRNRQ><TRNUID>TRAN_UID_PINCHRQ_0002<PINCHRQ><USERID>%s<NEWUSERPASS>%s</PINCHRQ></PINCHTRNRQ>' % (params['USERID'], params['NEWUSERPASS'])
# 
    def pmtcancrq(self, params):
        return '<PMTTRNRQ><TRNUID>BP_PMTCANC_1<PMTCANCRQ><SRVRTID>%s</PMTCANCRQ></PMTTRNRQ>' %(params['payeelstid'])
     
    def pmtinqrq(self, params):
        return '<PMTTRNRQ><TRNUID>BP_PMTCANC_1<PMTCANCRQ><SRVRTID>%s</PMTCANCRQ></PMTTRNRQ>' %(params['payeelstid'])
     
    def pmtmodrq(self, params):
        addressTag = self.generateAddressData(params['address'])
        frBankDetail = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['bankid'], params['bankid'], params['bankid'])
        return '<PMTTRNRQ><TRNUID>BP_PAYMENTMOD_1<PMTMODRQ><SRVRTID>%s<PMTINFO>%s<TRNAMT>%s<PAYEE>%s</PAYEE><PAYACCT>%s<DTDUE>%s</PMTINFO></PMTMODRQ></PMTTRNRQ>' %(params['payeelstid'], frBankDetail, params['trnamt'], params['addressTag'], params['payacct'], params['dtdue'])
     
    def pmtrq(self, params):
        addressTag = self.generateAddressData(params['address'])
        frBankDetail = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['bankid'], params['bankid'], params['bankid'])
        return '<PMTTRNRQ><TRNUID>BP_PAYMENT_1<PMTRQ><PMTINFO>%s<TRNAMT>%s<PAYEE>%s</PAYEE><PAYACCT>%s<DTDUE>%s</PMTINFO></PMTRQ></PMTTRNRQ>' %(frBankDetail, params['trnamt'], params['addressTag'], params['payacct'], params['dtdue'])
     
    def pmtsyncrq(self, params):
        bankDetailTag = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['bankid'], params['bankid'], params['bankid'])
        return '<PMTSYNCRQ><REFRESH>Y<REJECTIFMISSING>N%s</PMTSYNCRQ>' %(bankDetailTag)    
      
    def profrq(self, params):
        return '<PROFTRNRQ><TRNUID>TRAN_UID_OFX_PROFRQ_FT_1<PROFRQ><CLIENTROUTING>MSGSET<DTPROFUP>19900101</PROFRQ></PROFTRNRQ>'   
     
    def recpmtcancrq(self, params):
        return '<RECPMTTRNRQ><TRNUID>BP_RECPMTCAN_1<RECPMTCANCRQ><RECSRVRTID>%s<CANPENDING>Y</RECPMTCANCRQ></RECPMTTRNRQ>' % (params['recsrvrtid'])
     
    def recpmtmodrq(self, params):
        addressTag = self.generateAddressData(params['address'])
        bankDetailTag = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['bankid'], params['bankid'], params['bankid'])
        return '<RECPMTTRNRQ><TRNUID>BP_RECPMTMOD_1<RECPMTMODRQ><RECSRVRTID>%s<RECURRINST><FREQ>%s</RECURRINST><PMTINFO>%s<TRNAMT>%s<PAYEE>%s</PAYEE><PAYACCT>%s<DTDUE>%s</PMTINFO><MODPENDING>Y</RECPMTMODRQ></RECPMTTRNRQ>' %(params['recsrvrtid'], params['recfrq'], bankDetailTag, params['trnamt'], addressTag,  params['payacct'],  params['dtdue'])
 
    def recpmtrq(self, params):
        addressTag = self.generateAddressData(params['address'])
        bankDetailTag = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['bankid'], params['bankid'], params['bankid'])
        return '<RECPMTTRNRQ><TRNUID>BP_RECPMT_1<RECPMTRQ><RECURRINST><FREQ>%s</RECURRINST><PMTINFO>%s<TRNAMT>%s<PAYEE>%s</PAYEE><PAYACCT>%s<DTDUE>%s</PMTINFO></RECPMTRQ></RECPMTTRNRQ>' %(params['recfrq'], bankDetailTag, params['trnamt'], addressTag,  params['payacct'],  params['dtdue'])
     
    def recpmtsyncrq(self, params):
        bankDetailTag = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['bankid'], params['bankid'], params['bankid'])
        return '<RECPMTSYNCRQ><REFRESH>Y<REJECTIFMISSING>N%s</RECPMTSYNCRQ>' %(bankDetailTag)    
     
    def sonrq(self, params):
        return '<SONRQ><DTCLIENT>%s<USERID>%s<USERPASS>%s<LANGUAGE>ENG<FI><ORG>DI<FID>%s</FI><APPID>Money<APPVER>1900</SONRQ>' % (time.strftime("%Y%m%d%H%M%S"), params['USERID'], params['USERPASS'],params['FID'])
     
    def stmtendrq(self, params):
        bankDetailTag = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['bankid'], params['bankid'], params['bankid'])
        return '<STMTENDTRNRQ><TRNUID>TRAN_UID_STMTENDRQ_0001a<STMTENDRQ>%s<DTSTART>%s<DTEND>%s</STMTENDRQ></STMTENDTRNRQ>'%(bankDetailTag, params['dtstart'], params['dtend'])
     
    def stmtrq(self, params):
        bankDetailTag = '<BANKACCTFROM><BANKID>%s<ACCTID>%s<ACCTTYPE>%s</BANKACCTFROM>' %(params['bankid'], params['bankid'], params['bankid'])
        return '<STMTTRNRQ><TRNUID>TRAN_UID_STMTRQ_0001a<STMTRQ>%s<INCTRAN><DTSTART>%s<DTEND>%s<INCLUDE>Y</INCTRAN></STMTRQ></STMTTRNRQ>'%(bankDetailTag, params['dtstart'], params['dtend'])
    
    def wrapincontainer(self, request, container):
        return '<%s>%s</%s>' % (container, request, container)
    
    def addOfxHeader(self, data):
        return 'OFXHEADER:100\nDATA:OFXSGML\nVERSION:102\nSECURITY:NONE\nENCODING:USASCII\nCHARSET:1252\nCOMPRESSION:NONE\nOLDFILEUID:NONE\nNEWFILEUID:NONE\n' + data

    def generateAddressData(self, addr):
        addrXml =''
        for field in addr:
            addrXml = addrXml + '<%s>%s' % (field, addr[addr])
        return addeXml

rq = Requests()

# ********************
# Exposed RF Libraries
# ********************

# def generate_acctinforq_req(uid, pwd, fiid):
#     return generate_ofx_request('acctinforq', 'SIGNUPMSGSRQV1', locals())

def generate_acctinforq_req(testData):
    return generate_ofx_request('acctinforq', 'SIGNUPMSGSRQV1', testData[0])


def generate_intrarq_req(testData):
#                          uid, pwd, fiid, frmbankid, frmacctid, frmaccttype, tobankid, toacctid, toaccttype, amnt, dtdue):
    return generate_ofx_request('intrarq', 'BANKMSGSRQV1', testData[0])

def generate_intrasyncrq_req(uid, pwd, fiid, bankid, acctid, accttype):
    return generate_ofx_request('intrasyncrq', 'BANKMSGSRQV1', locals())

def generate_payeedelrq_req(uid, pwd, fiid, payeelstid):
    return generate_ofx_request('payeedelrq', 'BILLPAYMSGSRQV1', locals())

def generate_payeemodrq_req(uid, pwd, fiid, payeelstid, address):
    return generate_ofx_request('payeemodrq', 'BILLPAYMSGSRQV1', locals())    

def generate_payeerq_req(uid, pwd, fiid, payacct, address):
    return generate_ofx_request('payeerq', 'BILLPAYMSGSRQV1', locals()) 

def generate_payeesyncrq_req(uid, pwd, fiid, payacct, address):
    return generate_ofx_request('payeesyncrq', 'BILLPAYMSGSRQV1', locals())

def generate_pinchrq_req(uid, pwd, fiid, newpass):
    sonrq=   rq.sonrq(locals())
    pinchrq= rq.pinchrq(uid, pwd, fiid, newpass)
    req= rq.wrapincontainer(sonrq+pinchrq, 'SIGNONMSGSRQV1')
    req= rq.wrapincontainer(req, 'OFX')
    return rq.addOfxHeader(req) 

def generate_pmtinqrq_req(uid, pwd, fiid, payeelstid):
    return generate_ofx_request('pmtinqrq', 'BILLPAYMSGSRQV1', locals())

def generate_pmtmodrq_req(uid, pwd, fiid, payeelstid, address, bankid, acctid, accttype, trnamt, payacct, dtdue):
    return generate_ofx_request('pmtmodrq', 'BILLPAYMSGSRQV1', locals())

def generate_pmtrq_req(uid, pwd, fiid, address, bankid, acctid, accttype, trnamt, payacct, dtdue):
    return generate_ofx_request('pmtrq', 'BILLPAYMSGSRQV1', locals())

def generate_pmtsyncrq_req(uid, pwd, fiid, bankid, acctid, accttype):
    return generate_ofx_request('pmtsyncrq', 'BILLPAYMSGSRQV1', locals())

def generate_profrq_req(uid, pwd, fiid):
    return generate_ofx_request('profrq', 'PROFMSGSRQV1', locals())    

def generate_recpmtcancrq_req(uid, pwd, fiid, recsrvrtid):
    return generate_ofx_request('recpmtcancrq', 'BANKMSGSRQV1', locals())

def generate_recpmtmodrq_req(uid, pwd, fiid, recsrvrtid, recfrq, address, bankid, acctid, accttype, trnamt, payacct, dtdue):
    return generate_ofx_request('recpmtmodrq', 'BILLPAYMSGSRQV1', locals())

def generate_recpmtrq_req(uid, pwd, fiid, recfrq, address, bankid, acctid, accttype, trnamt, payacct, dtdue):
    return generate_ofx_request('recpmtrq', 'BILLPAYMSGSRQV1', locals())    

def generate_recpmtsyncrq_req(uid, pwd, fiid, bankid, acctid, accttype):
    return generate_ofx_request('recpmtsyncrq', 'BILLPAYMSGSRQV1', locals())

def generate_sonrq_req(dataID):
    sonrq= rq.sonrq(locals()['dataID'])
    req= rq.wrapincontainer(sonrq, 'SIGNONMSGSRQV1')
    req= rq.wrapincontainer(req, 'OFX')
    return rq.addOfxHeader(req)
   
  
def generate_stmtendrq_req(uid, pwd, fiid, bankid, acctid, accttype, dtstart, dtend):
    return generate_ofx_request('stmtendrq', 'BANKMSGSRQV1', locals())

def generate_stmtrq_req(uid, pwd, fiid, bankid, acctid, accttype, dtstart, dtend):
    return generate_ofx_request('stmtrq', 'BANKMSGSRQV1', locals())

# def generate_ofx_request(requestName, requestType, params):
#     rqinst = globals().get('rq')
#     func = getattr(rqinst, requestName)
#     sonrq=   rq.sonrq(params)
#     req= rq.wrapincontainer(sonrq, 'SIGNONMSGSRQV1')
#     bpdata = func(params)
#     req= req + rq.wrapincontainer(bpdata, requestType)
#     req= rq.wrapincontainer(req, 'OFX')
#     return rq.addOfxHeader(req) 

def generate_ofx_request(requestName, requestType, params):
    rqinst = globals().get('rq')
    func = getattr(rqinst, requestName)
    sonrq=   rq.sonrq(params)
    req= rq.wrapincontainer(sonrq, 'SIGNONMSGSRQV1')
    bpdata = func(params)
    req= req + rq.wrapincontainer(bpdata, requestType)
    req= rq.wrapincontainer(req, 'OFX')
    return rq.addOfxHeader(req) 

def prepare_TestData_for_ofx(dataPath, datasheet):
#     "C:/Users/307096/ddesilva_DI/ddesilva_DI/depot/development/software/RobotFramework/main/DI_Resources/test_data/ofx/testData.xlsx"
    dr = dataReader(dataPath, datasheet)
# print generate_sonrq_Req('uid', 'pwd', 'fiid', 'frmbankid', 'frmacctid', 'frmaccttype', 'tobankid', 'toacctid', 'toaccttype', 'amnt', 'dtdue')
    dr.readData()  

  
