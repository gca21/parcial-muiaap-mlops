import csv
from pathlib import Path
import joblib
from clasificador_paquetes.contracts import Entrada, Salida
import pandas as pd
from pydantic import ValidationError


def leer_csv(ruta: Path) -> list[Entrada]:
    entradas = []
    with open(ruta, "r") as f:
        data = csv.DictReader(f)
        for row in data:
            entradas.append(Entrada(**row))
    if len(entradas) == 0:
        raise ValueError
    return entradas


def preprocesar(entrada: Entrada) -> list[float]:
    return [
        round(entrada.peso_kg, 1),
        entrada.distancia_km
    ]


def cargar_modelo(ruta: Path):
    model = joblib.load(ruta)
    return model


def predecir(entrada: Entrada, modelo) -> Salida:
    features = preprocesar(entrada)
    category = modelo.predict([features])[0]
    pred_proba = max(modelo.predict_proba([features])[0])
    return Salida(
        id_paquete=entrada.id_paquete,
        categoria=category,
        confianza=pred_proba
    )


def guardar_csv(resultados: list[Salida], ruta: Path) -> None:
    ruta.parent.mkdir(parents=True, exist_ok=True)
    df = pd.DataFrame(columns=["id_paquete", "categoria", "confianza"])
    for result in resultados:
        entry = pd.DataFrame.from_dict({
            "id_paquete": [result.id_paquete],
            "categoria":  [result.categoria],
            "confianza": [result.confianza]
        })
        df = pd.concat([df, entry], ignore_index=True)
    df.to_csv(ruta, index=False)


def ejecutar(entrada: Path, modelo: Path, salida: Path) -> None:
    input = leer_csv(entrada)
    model = cargar_modelo(modelo)

    output = []
    # Try-except para prevenir salida parcial
    try:
        for row in input:
            pred = predecir(row, model)
            output.append(pred)
    except ValidationError as e:
        print(e)
        raise e
    guardar_csv(output, salida)


if __name__ == "__main__":
    ejecutar(
        Path("data/raw/paquetes.csv"),
        Path("models/modelo.joblib"),
        Path("resultados.csv"),
    )
