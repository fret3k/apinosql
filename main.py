from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from firebase_admin import credentials, firestore, initialize_app
from datetime import datetime

# Inicializar Firebase
cred = credentials.Certificate(
    r"C:\Users\fret\Documents\clavesJson\dbperson-d08a2-firebase-adminsdk-vfgya-280335fca1.json")
initialize_app(cred)
db = firestore.client()

# Referencia a la colección
person_ref = db.collection('apiPerson')


# Esquema de Persona
class Person(BaseModel):
    id: str = None
    nombre: str
    apellidos: str
    dni: str
    genero: bool
    fechaRegistro: str = None
    modificRegistro: str = None


app = FastAPI()

# Configurar CORS para permitir solicitudes desde el frontend (puedes agregar más dominios si es necesario)
origins = [
    "http://localhost:4200",  # Permitir solicitudes desde tu aplicación Angular (puedes agregar más)
    "http://localhost:3000",  # Si estás usando otro puerto
]

# Añadir el middleware de CORS a tu aplicación FastAPI
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,  # Permite solicitudes desde los dominios especificados
    allow_credentials=True,
    allow_methods=["*"],  # Permitir todos los métodos HTTP (GET, POST, PUT, DELETE, etc.)
    allow_headers=["*"],  # Permitir todos los encabezados
)


def create_response(type: str, message: str, data: dict = None):
    return {
        "type": type,
        "message": message,
        "data": data
    }


# Crear persona
@app.post("/person/", response_model=dict)
async def create_person(person: Person):
    try:
        person.fechaRegistro = datetime.now().isoformat()
        person.modificRegistro = datetime.now().isoformat()
        doc_ref = person_ref.document(person.id if person.id else None)
        doc_ref.set(person.dict(exclude={"id"}))
        return create_response("success", "Persona creada exitosamente", data={"id": doc_ref.id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=create_response("error", str(e)))


# Leer todas las personas
@app.get("/person/", response_model=dict)
async def get_all_persons():
    try:
        persons = [doc.to_dict() | {"id": doc.id} for doc in person_ref.stream()]
        return create_response("success", "Personas obtenidas exitosamente", data=persons)
    except Exception as e:
        raise HTTPException(status_code=500, detail=create_response("error", str(e)))


# Leer persona por ID
@app.get("/person/{person_id}", response_model=dict)
async def get_person(person_id: str):
    try:
        doc = person_ref.document(person_id).get()
        if not doc.exists:
            raise HTTPException(status_code=404, detail=create_response("warnig", "Persona no encontrada"))
        return create_response("success", "Persona obtenida exitosamente", data=doc.to_dict() | {"id": doc.id})
    except Exception as e:
        raise HTTPException(status_code=500, detail=create_response("error", str(e)))


# Actualizar persona
@app.put("/person/{person_id}", response_model=dict)
async def update_person(person_id: str, person: Person):
    try:
        doc_ref = person_ref.document(person_id)
        existing_doc = doc_ref.get()
        if not existing_doc.exists:
            raise HTTPException(status_code=404, detail=create_response("warnig", "Persona no encontrada"))

        existing_data = existing_doc.to_dict()
        person.modificRegistro = datetime.now().isoformat()

        doc_ref.update(person.dict(exclude={"id"}, exclude_unset=True))

        return create_response("success", "Persona actualizada exitosamente")
    except Exception as e:
        raise HTTPException(status_code=500, detail=create_response("error", str(e)))


# Eliminar persona
@app.delete("/person/{person_id}", response_model=dict)
async def delete_person(person_id: str):
    try:
        doc_ref = person_ref.document(person_id)
        if not doc_ref.get().exists:
            raise HTTPException(status_code=404, detail=create_response("warnig", "Persona no encontrada"))
        doc_ref.delete()
        return create_response("success", "Persona eliminada exitosamente")
    except Exception as e:
        raise HTTPException(status_code=500, detail=create_response("error", str(e)))
