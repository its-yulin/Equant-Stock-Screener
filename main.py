from flask import Flask, render_template, flash, request, make_response, jsonify, redirect
import yahoo_fin.stock_info as si
import random
import csv
import yfinance as yf
import plotly.graph_objs as graph
import pandas as pd
from alpha_vantage.timeseries import TimeSeries
from alpha_vantage.techindicators import TechIndicators
from alpha_vantage.sectorperformance import SectorPerformances
import os
from flask_login import login_user, logout_user, login_required, current_user
from flask_sqlalchemy import SQLAlchemy
from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
import matplotlib.pyplot as plt
#pip install -U kaleido
app = Flask(__name__)
from flask_login import UserMixin
db=SQLAlchemy(app)
class User(UserMixin,db.Model):

    id=db.Column(db.Integer,primary_key=True)
    username=db.Column(db.String(15))
    password=db.Column(db.String(128))
    real_name=db.Column(db.String(64))
    phone=db.Column(db.String(64),unique=True,nullable=False)

class WatchInfo(db.Model):

    id=db.Column(db.Integer,primary_key=True)
    userid=db.Column(db.Integer)
    stockid=db.Column(db.String(15))
basedir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(basedir,'app.sqlite')
app.config['SQLALCHEMY_COMMIT_ON_TEARDOWN'] = True
app.config['SQLALCHEMY_TRACK_MODIFICATIONS']=False
db.create_all()
login_manager = LoginManager(app)
login_manager.login_view = 'login'


app.secret_key = 'secret string'

@app.route('/person', methods=['GET'])
def person():
    return render_template('person.html')
 

@app.route('/signup', methods=['POST', 'GET'])
def signup():
    if request.method=="GET":
          return render_template('signup.html')
    username = request.form['username']
    password = request.form['password']
    password2 = request.form['password2']
    phone = request.form['phone']
    real_name = request.form['real_name']

    if password != password2:
        return render_template(
            'signup.html',
             msg="Please re-enter the same password."
        )

    user = User.query.filter_by(phone=phone).first()
    if user is not None:
        return render_template(
            'signup.html',
          msg="Phone number already registered."
        )
    user = User(username=username, password=password,phone=phone,real_name=real_name)
    db.session.add(user)
    db.session.commit()
    return redirect("/login")

@app.route('/login', methods=['POST', 'GET'])
def login():
    if request.method=="GET":
          return render_template('login.html')
    username = request.form['username']
    password = request.form['password']

    user = User.query.filter_by(username=username).first()

    if user and password == user.password:
        login_user(user)
 
        return redirect("/")
    return render_template(
            'login.html',
          msg="Wrong user name or password."
        )
   

@app.route("/logout")
def logout():
    logout_user()
    return redirect("/login")

@app.route('/contrastlist', methods=['GET'])
def contrastlistView():
    stock1=request.args.get("stock1")
    stock2=request.args.get("stock2")
    if stock1 is None or stock2 is None:
        return render_template("contrastlist.html",data=None)

    # retrieve basic info on the stock
    try:
        quote_table1 = si.get_quote_table(stock1)
        quote_table2 = si.get_quote_table(stock2)
    except:
        return render_template("contrastlist.html",data=None,msg="Incorrect stock name.")

    PE_ratio1 = quote_table1["PE Ratio (TTM)"]
    
    Ask1 = quote_table1["Ask"]
    Bid1 = quote_table1["Bid"]
    Volume1 = quote_table1["Volume"]
    Open1 = quote_table1["Open"]
    Previous_Close1 = quote_table1["Previous Close"]
    Beta1 = quote_table1["Beta (5Y Monthly)"]
    Market_Cap1 = quote_table1["Market Cap"]

    PE_ratio2 = quote_table2["PE Ratio (TTM)"]

    Ask2 = quote_table2["Ask"]
    Bid2 = quote_table2["Bid"]
    Volume2= quote_table2["Volume"]
    Open2 = quote_table2["Open"]
    Previous_Close2 = quote_table2["Previous Close"]
    Beta2 = quote_table2["Beta (5Y Monthly)"]
    Market_Cap2 = quote_table2["Market Cap"]
    data={}
    dict1={"value1":PE_ratio1,"value2":PE_ratio2}
    if PE_ratio1>PE_ratio2:
        dict1["color"]=1
    else:
        dict1["color"]=-1
    data["PE_ratio"]=dict1
    dict1={"value1":Ask1,"value2":Ask2,"color":0}
    data["Ask"]=dict1
    dict1={"value1":Bid1,"value2":Bid2,"color":0}
    data["Bid"]=dict1
    dict1={"value1":Volume1,"value2":Volume2}
    if Volume1>Volume2:
        dict1["color"]=1
    else:
        dict1["color"]=-1
    data["Volume"]=dict1
    dict1={"value1":Open1,"value2":Open2}
    if Open1>Open2:
        dict1["color"]=1
    else:
        dict1["color"]=-1
    data["Open"]=dict1
    dict1={"value1":Previous_Close1,"value2":Previous_Close2}
    if Previous_Close1>Previous_Close2:
        dict1["color"]=1
    else:
        dict1["color"]=-1
    data["Previous_Close"]=dict1
    dict1={"value1":Beta1,"value2":Beta2}
    if Beta1>Beta2:
        dict1["color"]=1
    else:
        dict1["color"]=-1
    data["Beta"]=dict1
    dict1={"value1":Market_Cap1,"value2":Market_Cap2,"color":0}
    data["Market_Cap"]=dict1

    data["stock1"]=stock1
    data["stock2"]=stock2
    return render_template("contrastlist.html",data=data)
@app.route('/watchlist', methods=['GET'])
def watchListView():
    stock=request.args.get("stock")
    watchlist = WatchInfo.query.filter_by(userid=current_user.id).all()

    if len(watchlist)==0:
          return render_template("watchlist.html",data=None)

    if stock is None:
        stock=watchlist[0].stockid


    watchlist2=[]
    for i in watchlist:
        price=si.get_live_price(i.stockid)
        price = round(price,4)
        watchlist2.append({"price":price,"stock":i.stockid})
    data=socket_data(stock)
    data["stock"]=stock
    return render_template("watchlist.html",data=data,watchlist=watchlist2)

@app.route('/watch', methods=['GET'])
def watchView():
    stock=request.args.get("stock")
    print("---------------------------------")
    watchinfo = WatchInfo.query.filter_by(userid=current_user.id,stockid=stock).first()
    if watchinfo is None:
        watchinfo = WatchInfo(userid=current_user.id,stockid=stock)
        db.session.add(watchinfo)
        db.session.commit()
        return  jsonify({"code":1})
    else:
        db.session.delete(watchinfo)
        db.session.commit()
        return  jsonify({"code":-1})

    
return_list = []
@app.route('/', methods=['POST', 'GET'])
def index():
    if request.method == 'POST':

        zhi = request.form.get('zhi')
        if(zhi=="search"):

            stock=request.form.get("stock")
            try:
                data=socket_data(stock)
            except:
                   return render_template("index.html",msg="not found")
    
            data["stock"]=stock
            try:
                watch = WatchInfo.query.filter_by(userid=current_user.id,stockid=stock).first()
                data["watchBtn"]=True
            except:
                watch=None
                data["watchBtn"]=False

            return render_template("index.html",data=data,stock=stock,watch=watch)

    img=""
    msg=request.args.get("msg")
    api_key = '6DYUFU9TTKWDXPZW'
    sp = SectorPerformances(key='api_key', output_format='pandas')
    data, meta_data = sp.get_sector()
    sectors = data['Rank A: Real-Time Performance']

    sectors = sectors.to_frame()

    Health_Care = round(sectors.loc['Health Care', 'Rank A: Real-Time Performance'],5)

    Utilities = round(sectors.loc['Utilities', 'Rank A: Real-Time Performance'], 5)

    Materials = round(sectors.loc['Materials', 'Rank A: Real-Time Performance'],5)

    Information_Technology = round(sectors.loc['Information Technology', 'Rank A: Real-Time Performance'],5)

    Real_Estate = round(sectors.loc['Real Estate', 'Rank A: Real-Time Performance'],5)

    Industrials = round(sectors.loc['Industrials', 'Rank A: Real-Time Performance'],5)

    Financials = round(sectors.loc['Financials', 'Rank A: Real-Time Performance'],5)

    Energy = round(sectors.loc['Energy', 'Rank A: Real-Time Performance'],5)

    eight_data_sector = ['', f"Health_Care: {Health_Care}", f"Utilities: {Utilities}", f"Materials: {Materials}",
                    f"Information_Technology: {Information_Technology}",
                    f"Real_Estate: {Real_Estate}", f"Industrials: {Industrials}", f"Financials: {Financials}",
                    f"Energy: {Energy}"]
    print(eight_data_sector)

    return render_template("index.html",data={"eight_data":eight_data_sector,"stock":"Sector Performance","watchBtn":False},recommendlist=False,msg=msg)

  

@app.route('/recommendlist', methods=['GET'])
def recommendlist():
    rec_list = pd.read_csv('stock_rec.csv')

    recommendlist = rec_list.loc[0:9, "Stock"].tolist()


    return  jsonify({"recommendlist":recommendlist})
@app.route('/ab', methods=['POST', 'GET'])
def filger():
    print("ab")
    froom = request.args.get("frrom")
    tooo = request.args.get("tooo")
    print("rt")
    print("%s-%s" % (froom, tooo))
    return_list.clear()

    rec_list = pd.read_csv('stock_rec.csv')

    for i in rec_list.values.tolist():
        print(i)
        if i[2] > int(froom) and i[2] < int(tooo):
            return_list.append(i[1])


    print(return_list)
    return jsonify({"Sd": return_list})


def socket_data(socket):

    #generate a random number
    sp=random.randint(1000,9000);

    #retrieve real-time price
    price = si.get_live_price(socket)

    # retrieve basic info on the stock
    quote_table = si.get_quote_table(socket)

    PE_ratio = quote_table["PE Ratio (TTM)"]

    Ask = quote_table["Ask"]

    Bid = quote_table["Bid"]

    Volume = quote_table["Volume"]

    Open = quote_table["Open"]

    Previous_Close = quote_table["Previous Close"]

    Beta = quote_table["Beta (5Y Monthly)"]

    Market_Cap = quote_table["Market Cap"]

    eight_data = ['', f"Previous Close: {Previous_Close}", f"Open: {Open}", f"Bid: {Bid}", f"Ask: {Ask}", f"Volume: {Volume}", f"Market Cap: {Market_Cap}", f"Beta (5Y Monthly): {Beta}",f"PE ratio: {PE_ratio}"]

    # plot of stock price
    StockData = yf.download(tickers=socket, period='90d', interval='1d', rounding=True)

    Sgraph = graph.Figure()
    Sgraph.add_trace(
        graph.Candlestick(x=StockData.index, open=StockData['Open'], high=StockData['High'], low=StockData['Low'],
                          close=StockData['Close'], name='market data'))
    Sgraph.update_layout(title=socket + '\'s share price', xaxis_title='Date', yaxis_title='Price')

    Sgraph.write_image("static/fig"+str(sp)+".png")

    image = "static/fig"+str(sp)+".png"


    price = round(price,4)

    data = {"price": price, "eight_data": eight_data, "image": image}

    return data




@login_manager.user_loader
def load_user(user_id):
  return User.query.get(int(user_id))




if __name__ == '__main__':

    # app.run(host='0.0.0.0', port=80, debug=True)
    app.run( debug=True)

