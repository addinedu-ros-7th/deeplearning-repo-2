# mysql module
import mysql.connector

# connect_database( hostname , username , password )
def connect_database(host_name="database-1.cxiiw8ugcoej.ap-northeast-2.rds.amazonaws.com", user_name="robot", user_password="robot"):
    mydb = mysql.connector.connect(
        host=host_name,
        port=3306,
        user=user_name,
        password=user_password,
        database="amrdb"
    )

    cursor = mydb.cursor()
    return mydb, cursor

def close_database(mydb, cursor):
    cursor.close()
    mydb.close()

def execute_query(query, params=None):  # params 추가
    mydb, cursor = connect_database()
    try:
        if params:
            cursor.execute(query, params)  # params 사용
        else:
            cursor.execute(query)

        if query.strip().lower().startswith("select"):
            return cursor.fetchall()
        else:
            mydb.commit()
            print("success!!!")
    except mysql.connector.Error as err:
        print(err)
        return []  # 오류 발생 시 빈 리스트 반환
    finally:
        close_database(mydb=mydb, cursor=cursor)
