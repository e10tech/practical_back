#このコードはFastAPIを使用して、顧客情報を管理するAPIを実装しているもの


from fastapi import FastAPI, HTTPException, Query
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
#pydanticはデータのバリデーションやシリアライズを行うためのライブラリ
#BaseModelはpydanticの基本クラスで、データモデルを定義するために使用される
import requests
import json
#↓のコードはつまりdb_controlパッケージのcrud.pyとmymodels.pyをインポートしている
#from db_control import crud, mymodels#ここがローカルのSQLであってMySQLにする場合はここを変更する必要がある
from db_control import crud, mymodels_MySQL


# CustomerクラスはpydanticのBaseModelを継承している
# 1. pydanticでできること
#    下のように書くだけで、型の定義とバリデーション（型チェック）が自動で行われる
# 2. 違う型が来た場合どうなる？
#    例えば age: int なのに文字列 "20" が来た場合、自動でintに変換できるものは変換してくれる
#    でも、変換できない値（例: age="abc"）が来た場合はエラーになる
# 3. カンマ（,）で区切る必要は？
#    pydanticのクラス定義ではカンマは不要
#    Pythonのクラスの属性定義なので、1行ごとに改行して書く

class Customer(BaseModel):
    customer_id: str
    customer_name: str
    age: int
    gender: str


app = FastAPI()

# CORSミドルウェアの設定
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def index():
    return {"message": "FastAPI top page!"}

"""
ここが課題3の新規顧客登録APIの動き
つまり、ここでidが空の場合は登録ができないようにする処理を追加すればいい
"""
@app.post("/customers")  # この関数は「/customers」エンドポイントにPOSTリクエストが来たときに呼ばれる
def create_customer(customer: Customer):  # リクエストのボディ（JSON）をCustomer型として受け取る
    values = customer.dict()  # 受け取ったCustomerオブジェクトを辞書型（Pythonのdict）に変換する

    #ここでバリデーションを追加して空のIDなら登録できないようにする
    if not values['customer_id']:  # customer_idが空文字列なら
        raise HTTPException(status_code=400, detail='customer_idは必須です')  # 400 Bad Requestエラーを返す

    tmp = crud.myinsert(mymodels_MySQL.Customers, values)  # その辞書データを使って、DBのCustomersテーブルに新しいレコードを挿入する
    result = crud.myselect(mymodels_MySQL.Customers, values.get("customer_id"))  # 登録したcustomer_idでDBからそのレコードを再取得する

    if result:  # もしレコードが取得できたら
        result_obj = json.loads(result)  # 取得したデータ（JSON文字列）をPythonのリストや辞書に変換する
        return result_obj if result_obj else None  # データがあれば返す。なければNone
    return None  # レコードが取得できなければNoneを返す


@app.get("/customers")
def read_one_customer(customer_id: str = Query(...)):
    result = crud.myselect(mymodels_MySQL.Customers, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    result_obj = json.loads(result)
    return result_obj[0] if result_obj else None


@app.get("/allcustomers")
def read_all_customer():
    result = crud.myselectAll(mymodels_MySQL.Customers)
    # 結果がNoneの場合は空配列を返す
    if not result:
        return []
    # JSON文字列をPythonオブジェクトに変換
    return json.loads(result)


@app.put("/customers")
def update_customer(customer: Customer):
    values = customer.dict()
    values_original = values.copy()
    tmp = crud.myupdate(mymodels_MySQL.Customers, values)
    result = crud.myselect(mymodels_MySQL.Customers, values_original.get("customer_id"))
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    result_obj = json.loads(result)
    return result_obj[0] if result_obj else None


@app.delete("/customers")
def delete_customer(customer_id: str = Query(...)):
    result = crud.mydelete(mymodels_MySQL.Customers, customer_id)
    if not result:
        raise HTTPException(status_code=404, detail="Customer not found")
    return {"customer_id": customer_id, "status": "deleted"}


@app.get("/fetchtest")
def fetchtest():
    response = requests.get('https://jsonplaceholder.typicode.com/users')
    return response.json()
