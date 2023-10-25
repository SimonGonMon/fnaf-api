import os
import psycopg2
import boto3
from fastapi import FastAPI, UploadFile, File, Form
from dotenv import load_dotenv
load_dotenv()

app = FastAPI()

# AWS S3 credentials
AWS_ACCESS_KEY = os.environ.get('AWS_ACCESS_KEY')
AWS_SECRET_ACCESS_KEY = os.environ.get('AWS_SECRET_ACCESS_KEY')
S3_BUCKET_NAME = 's-cuadrado-bucket'
S3_FOLDER_NAME = 'simon-al-cuadrado'

# PostgreSQL credentials
DB_USER = os.environ.get('DB_USER')
DB_PASSWORD = os.environ.get('DB_PASSWORD')
DB_PORT = os.environ.get('DB_PORT')
DB_DATABASE = os.environ.get('DB_DATABASE')
DB_HOST = os.environ.get('DB_HOST')

# Initialize S3 client
s3_client = boto3.client('s3', aws_access_key_id=AWS_ACCESS_KEY, aws_secret_access_key=AWS_SECRET_ACCESS_KEY)

# Initialize PostgreSQL connection
conn = psycopg2.connect(user=DB_USER, password=DB_PASSWORD, host=DB_HOST, port=DB_PORT, dbname=DB_DATABASE)
cursor = conn.cursor()

@app.post("/animatronics/upload")
async def upload_file(file: UploadFile = File(...)):
    # Extract file name from UploadFile object
    file_name = file.filename

    # Save file to S3
    s3_client.upload_fileobj(file.file, S3_BUCKET_NAME, f"{S3_FOLDER_NAME}/{file_name}")

     # Capitalize first letter of each word and remove file extension
    file_name = " ".join([word.capitalize() for word in file_name.split(" ")])[:-len(file_name.split(".")[-1])-1]

    # Save file name, game name, and year to PostgreSQL
    cursor.execute("INSERT INTO \"s-cuadrado\" (nombre, juego, año) VALUES (%s, %s, %s)", (file_name, "FNAF 7", 2024))
    conn.commit()

    return {"message": "File uploaded successfully"}


@app.get("/animatronics/game/{number}")
async def get_animatronics_by_game_number(number: int):
    # Fetch animatronics by game number
    cursor.execute("SELECT * FROM \"s-cuadrado\" WHERE juego LIKE %s", ("FNAF " + str(number) + "%",))
    animatronics = cursor.fetchall()
    print(animatronics)

    # Format animatronics as a list of dictionaries
    animatronics_list = []
    for animatronic in animatronics:
        animatronics_list.append({
            "id": animatronic[0],
            "nombre": animatronic[1],
            "juego": animatronic[2],
            "año": animatronic[3]
        })

    return {"animatronics": animatronics_list}


@app.get("/")
async def root():
    return {"message": "Hello World"}


@app.get("/hello/{name}")
async def say_hello(name: str):
    return {"message": f"Hello {name}"}


@app.delete("/debug/delete-all")
async def delete_all_objects_s3():
    # List all objects in the folder
    objects = s3_client.list_objects_v2(Bucket=S3_BUCKET_NAME, Prefix=f"{S3_FOLDER_NAME}/")

    # Delete all objects in the folder
    if 'Contents' in objects:
        delete_keys = [{'Key': obj['Key']} for obj in objects['Contents']]
        s3_client.delete_objects(Bucket=S3_BUCKET_NAME, Delete={'Objects': delete_keys})

    return {"message": "All objects deleted successfully"}
