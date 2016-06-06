import urllib.request, json, re, csv, codecs
from flask import Flask, request, render_template
from operator import itemgetter

def totalBalance(amount,balance):
    balance += amount
    return balance

def sortDataByDate(data):
    # print("In sortDataByDate with data" )
    for i in range(len(data)):
        date = int(re.sub(r'-','',data[i]['date']))
        data[i]['newDate'] = date
        data[i]['company'] = data[i]['company'].capitalize()
    newData = sorted(data, key=itemgetter('newDate'), reverse=True)
    # print("NewData is :::", newData)
    for d in newData:
        del d['newDate']
    return newData

def sortDataByLedger(data):
    # print("In sortDataByLedger with data" )
    for i in range(len(data)):
        date = int(re.sub(r'-','',data[i]['date']))
        data[i]['newDate'] = date
    newData = sorted(data, key=lambda k: (k['ledger'].lower(), -k['newDate']))
    for d in newData:
        del d['newDate']
    return newData

def getTransactions(disp):
    notComplete = True
    pageNo = 1
    totalTransactions = 0
    balance = 0
    transactions = list()
    reader = codecs.getreader("utf-8")
    while notComplete:
        url = "http://resttest.bench.co/transactions/" + str(pageNo) + ".json"
        response = urllib.request.urlopen(url)
        data = json.load(reader(response))
        # print("page is ",data['page'])
        noOfTransactions = len(data['transactions'])
        # print("transactions length",noOfTransactions)
        totalTransactions += noOfTransactions
        for i in range(noOfTransactions):
            date = data['transactions'][i]['Date']
            ledger = data['transactions'][i]['Ledger']
            amount = float(data['transactions'][i]['Amount'])
            company = data['transactions'][i]['Company']
            # print "date is ",date," ledger is ",ledger," amount is ",amount," company is ",company
            # balance = totalBalance(amount,balance)
            transactions.append({'date':date,'ledger':ledger,'amount':amount,'company':company})
        if (totalTransactions == int(data['totalCount'])):
            notComplete = False
        else:
            pageNo +=1

    # cleanedData = [dict(tupleized) for tupleized in set(tuple(item.items()) for item in transactions)]
    if disp == 'all':
        for i in range(len(transactions)):
            # print("date is ",transactions[i]['date']," ledger is ",transactions[i]['ledger']," amount is ",transactions[i]['amount']," company is ",transactions[i]['company'])
            balance = totalBalance(transactions[i]['amount'],balance)
        return (transactions,balance,'All Transactions')
    elif disp == 'clean' or disp == 'duplicate':
        cleanedSet = set()
        cleanedData = list()
        duplicateData = list()
        for i in range(len(transactions)):
            tup = tuple(transactions[i].items())
            # print "is subset", tup.issubset(cleanedData)
            if tup in cleanedSet:
                duplicateData.append(transactions[i])
                # print("Duplicate Data: ", tup)
            else:
                cleanedSet.add(tup)
                cleanedData.append(transactions[i])

        if disp == 'duplicate':
            for i in range(len(duplicateData)):
                balance = totalBalance(duplicateData[i]['amount'],balance)
            return (duplicateData,balance,'Duplicate Transactions')

        for i in range(len(cleanedData)):
            # print(i,": ",cleanedData[i]['company'])
            cleanedData[i]['company'] = re.sub(r'\s(@|-|/)\s',' ',cleanedData[i]['company'])
            creditcardMatch = re.search(r'\sx+\d+\.?\d*',cleanedData[i]['company'])
            if creditcardMatch:
                cleanedData[i]['company'] = re.sub(r'\sx+\d+\.?\d*',' ',cleanedData[i]['company'])
            cleanedData[i]['company'] = re.sub(r' +',' ',cleanedData[i]['company'])
            cleanedData[i]['company'] = re.sub(r'\s\b\d+\.?\d*\b',' ',cleanedData[i]['company'])
            cleanedData[i]['company'] = re.sub(r'\s\#[A-Za-z0-9]*\s',' ',cleanedData[i]['company'])
            replaceWords = ['THANK','YOU','PAIEMENT','MERCI','RECEIVED','POSTAL']
            for word in replaceWords:
                cleanedData[i]['company'] = cleanedData[i]['company'].replace(word,' ')
            with open('canada&usstates.csv', 'r') as csvfile:
                f = csv.reader(csvfile, delimiter=',')
                compList = cleanedData[i]['company'].split(' ')
                compInit = compList[0]
                if len(compList) > 1:
                    # comp = ' '.join(compList[-len(compList)])
                    compList.pop(0)
                    # print compList
                    comp = ' '.join(compList)
                    for row in f:
                        prov = row[0]
                        # print "comp is ", comp
                        if (re.search(r'\b%s\b' %prov,comp)):
                            cleanedData[i]['company'] = compInit + ' ' + re.sub(r'\b%s\b' %prov,' ',comp)
            cleanedData[i]['company'] = re.sub(r' +',' ',cleanedData[i]['company'])
            # print i,": ",cleanedData[i]['company']
            with open('canadacities.csv','r') as csvfile:
                f = csv.reader(csvfile,delimiter=',')
                compList = cleanedData[i]['company'].split(' ')
                compInit = compList[0]
                if len(compList) > 1:
                    compList.pop(0)
                    # print compList
                    comp = ' '.join(compList)
                    # print "comp is ",comp
                    for row in f:
                        city = row[1]
                        if (re.search(r'\b%s\b' %city,comp,re.I)):
                            # print "city found", city
                            compTemp = re.sub(r'\s\#?[A-Za-z0-9]+\s\b%s\b' %city,' ',comp,flags=re.I)
                            compTemp = re.sub(r'\b%s\b' %city,' ',comp,flags=re.I)
                            cleanedData[i]['company'] = compInit + ' ' + compTemp
            cleanedData[i]['company'] = re.sub(r' +',' ',cleanedData[i]['company'])
            # print i,": ",cleanedData[i]['company']
            with open('currencies.csv','r') as csvfile:
                f = csv.reader(csvfile,delimiter=',')
                next(f)
                compList = cleanedData[i]['company'].split(' ')
                compInit = compList[0]
                if len(compList) > 1:
                    compList.pop(0)
                    # print compList
                    comp = ' '.join(compList)
                    for row in f:
                        # print "row is ",row
                        currCode = row[1]
                        if (re.search(r'\b%s\b' %currCode,cleanedData[i]['company'])):
                            currTemp = re.sub(r'\b%s\b' %currCode,' ',comp,flags=re.I)
                            cleanedData[i]['company'] = compInit + ' ' + currTemp
            # print(i,": ",cleanedData[i]['company'])

            balance = totalBalance(cleanedData[i]['amount'],balance)
        # print("balance is", balance)
        return(cleanedData,balance,'Clean Transactions')

app = Flask(__name__)

@app.route("/",methods=['POST', 'GET'])
def main():
    # print("In main")
    if (request.method == 'POST'):
        if request.form['submit'] == 'submit':
            return flask.redirect(flask.url_for('dispTransactions'))
    elif (request.method == 'GET'):
        return render_template('index.html')


@app.route('/transactions',methods=['GET', 'POST'])
def dispTransactions():
    disp =  request.form['options']
    # print("trying to redirect to get ",disp)
    if disp == 'sortByLedger' or disp == 'clean' or disp == 'sortByDate':
        (data, balance, dispName) = getTransactions('clean')
    else:
        (data, balance, dispName) = getTransactions(disp)

    if disp == 'sortByLedger':
        data = sortDataByLedger(data)
        prev_ledger = 'unknown'
        ledgerTotal = list()
        bal = 0
        for i in range(len(data)):
            if (data[i]['ledger'] == prev_ledger):
                bal = bal + data[i]['amount']
                prev_ledger = data[i]['ledger']
            else:
                if (prev_ledger != 'unknown'):
                    bal = round(bal,2)
                    ledgerTotal.append({'ledger':prev_ledger,'balance':bal})
                prev_ledger = data[i]['ledger']
                bal = data[i]['amount']
        return render_template('disp3.html',entries = ledgerTotal,data=data,disp='Totals by Category',balance=balance)
    elif disp == 'sortByDate':
        data = sortDataByDate(data)
        prev_date = 'unknown'
        dateTotal = list()
        bal = 0
        for i in range(len(data)):
            if (data[i]['date'] == prev_date):
                bal = bal + data[i]['amount']
                prev_date = data[i]['date']
            else:
                if (prev_date != 'unknown'):
                    bal = round(bal,2)
                    dateTotal.append({'date':prev_date,'balance':bal})
                prev_date = data[i]['date']
                bal = data[i]['amount']
        return render_template('disp4.html',entries = dateTotal,disp='Running Balance',balance=balance)
    else:
        data = sortDataByDate(data)
        # print("Data is ::", data)
        # print("header is ::",list(data[0].keys()))
        return render_template('disp2.html',entries = data,disp=dispName,balance=balance)



if __name__ == "__main__":
    app.run()

# print data
