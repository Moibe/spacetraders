"""Regenera `spacetraders/models.py` desde el OpenAPI oficial de SpaceTraders.

El spec oficial (github.com/SpaceTradersAPI/api-docs) parte los modelos en un
archivo JSON Schema por entidad y los referencia con `$ref` relativos
(`./Ship.json`). datamodel-code-generator no resuelve esos refs entre archivos
manteniendo buenos nombres de clase, asi que aca se hace en tres pasos:

    1. clonar (o actualizar) el repo del spec
    2. juntar los 76 modelos en un solo OpenAPI con `components.schemas`
    3. generar un unico modulo pydantic v2

Uso:

    python tools/generate_models.py
    python tools/generate_models.py --keep-clone /ruta/al/clon
"""

from __future__ import annotations

import argparse
import json
import pathlib
import shutil
import subprocess
import sys
import tempfile

REPO_SPEC = "https://github.com/SpaceTradersAPI/api-docs.git"
RAIZ = pathlib.Path(__file__).resolve().parent.parent
DESTINO = RAIZ / "spacetraders" / "models.py"

CABECERA = '''"""Modelos de la API de SpaceTraders (v{version}).

ARCHIVO GENERADO -- no editar a mano.
Se genera desde el OpenAPI oficial (github.com/SpaceTradersAPI/api-docs) con:

    python tools/generate_models.py

Los campos usan snake_case en Python y alias camelCase para la API, asi que al
serializar hacia la API hay que usar `.model_dump(by_alias=True)`.
"""
'''


def clonar_spec(destino: pathlib.Path) -> pathlib.Path:
    """Clona el repo del spec (shallow) o actualiza el clon que ya exista."""
    if (destino / ".git").exists():
        print(f"actualizando clon en {destino}")
        subprocess.run(["git", "-C", str(destino), "pull", "--ff-only", "-q"], check=True)
    else:
        print(f"clonando {REPO_SPEC}")
        subprocess.run(
            ["git", "clone", "--depth", "1", "-q", REPO_SPEC, str(destino)], check=True
        )
    return destino


def reescribir_refs(nodo: object) -> object:
    """Convierte `$ref: ./Ship.json` en `$ref: #/components/schemas/Ship`."""
    if isinstance(nodo, dict):
        ref = nodo.get("$ref")
        if isinstance(ref, str) and ref.endswith(".json"):
            return {"$ref": f"#/components/schemas/{pathlib.PurePosixPath(ref).stem}"}
        return {k: reescribir_refs(v) for k, v in nodo.items()}
    if isinstance(nodo, list):
        return [reescribir_refs(v) for v in nodo]
    return nodo


def empaquetar(models_dir: pathlib.Path, salida: pathlib.Path, version: str) -> int:
    """Junta los JSON Schema sueltos en un OpenAPI autocontenido."""
    schemas: dict[str, object] = {}
    for archivo in sorted(models_dir.glob("*.json")):
        schema = json.loads(archivo.read_text(encoding="utf-8"))
        schema.pop("$schema", None)
        # El `title` interno pisaria el nombre de clase que viene del nombre de archivo.
        schema.pop("title", None)
        schemas[archivo.stem] = reescribir_refs(schema)

    salida.write_text(
        json.dumps(
            {
                "openapi": "3.0.3",
                "info": {"title": "SpaceTraders models", "version": version},
                "paths": {},
                "components": {"schemas": schemas},
            },
            indent=1,
        ),
        encoding="utf-8",
    )
    return len(schemas)


def version_del_spec(repo: pathlib.Path) -> str:
    spec = json.loads((repo / "reference" / "SpaceTraders.json").read_text(encoding="utf-8"))
    return str(spec.get("info", {}).get("version", "desconocida"))


def generar(bundle: pathlib.Path, destino: pathlib.Path, version: str) -> None:
    """Corre datamodel-codegen y le pone la cabecera estable al resultado."""
    subprocess.run(
        [
            sys.executable,
            "-m",
            "datamodel_code_generator",
            "--input",
            str(bundle),
            "--input-file-type",
            "openapi",
            "--output",
            str(destino),
            "--output-model-type",
            "pydantic_v2.BaseModel",
            "--target-python-version",
            "3.11",
            "--use-schema-description",
            "--use-standard-collections",
            "--use-union-operator",
            "--snake-case-field",
            "--allow-population-by-field-name",
            "--formatters",
            "black",
        ],
        check=True,
    )

    cuerpo = destino.read_text(encoding="utf-8").split("\n")
    # Se descarta la cabecera de codegen porque incluye un timestamp y ensuciaria
    # el diff en cada regeneracion.
    while cuerpo and cuerpo[0].startswith("#"):
        cuerpo.pop(0)
    destino.write_text(
        CABECERA.format(version=version) + "\n".join(cuerpo), encoding="utf-8"
    )


def main(argv: list[str] | None = None) -> int:
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument(
        "--keep-clone",
        type=pathlib.Path,
        help="directorio donde dejar el clon del spec (default: temporal)",
    )
    args = parser.parse_args(argv)

    temporal = args.keep_clone is None
    base = pathlib.Path(tempfile.mkdtemp(prefix="st-spec-")) if temporal else args.keep_clone
    repo = base / "api-docs" if temporal else base

    try:
        clonar_spec(repo)
        version = version_del_spec(repo)
        bundle = base / "bundled.json"
        cantidad = empaquetar(repo / "models", bundle, version)
        print(f"{cantidad} schemas empaquetados (spec {version})")
        generar(bundle, DESTINO, version)
        lineas = len(DESTINO.read_text(encoding="utf-8").split("\n"))
        print(f"{DESTINO.relative_to(RAIZ)} regenerado: {lineas} lineas")
    finally:
        if temporal:
            shutil.rmtree(base, ignore_errors=True)
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
