#!/usr/bin/env python3
"""Build the portfolio site from your public GitHub repositories.

Reads every repo (languages, file tree, manifests, README), detects the tech
stack, and writes a static site to _site/:

    _site/                 copy of site/ (HTML, CSS, JS)
    _site/data/projects.json
    _site/readmes/<repo>.html   rendered README (images/links made absolute)

Usage:
    GITHUB_TOKEN=$(gh auth token) python3 scripts/build.py
    python3 scripts/build.py --readme-drafts   # also write README drafts for
                                               # repos that don't have one

Only the Python standard library is used.
"""
from __future__ import annotations

import argparse
import json
import os
import posixpath
import re
import shutil
import sys
import time
import urllib.error
import urllib.parse
import urllib.request
from concurrent.futures import ThreadPoolExecutor
from datetime import datetime, timezone
from html import escape
from html.parser import HTMLParser
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
CONFIG_PATH = ROOT / "portfolio.config.json"
SITE_SRC = ROOT / "site"
OUT = ROOT / "_site"
DRAFTS = ROOT / "readme-drafts"

TOKEN = os.environ.get("GITHUB_TOKEN") or os.environ.get("GH_TOKEN")
API = "https://api.github.com"
RAW = "https://raw.githubusercontent.com"

# --------------------------------------------------------------------------
# Stack knowledge base
# --------------------------------------------------------------------------

# label -> group. Groups decide display order on the cards.
GROUP_ORDER = ["framework", "ai", "ml", "data", "lang", "db", "ui", "infra", "tool", "test"]
LABELS: dict[str, str] = {}


def _reg(group: str, *labels: str) -> None:
    for label in labels:
        LABELS[label] = group


_reg("framework", "React Native", "Expo", "Next.js", "React", "Vue", "Angular", "Svelte",
     "Express", "NestJS", "Fastify", "Koa", "FastAPI", "Flask", "Django", "Streamlit",
     "Gradio", "Electron", "Flutter")
_reg("ai", "LangChain", "LangGraph", "CrewAI", "OpenAI", "Anthropic", "MCP", "LlamaIndex",
     "Hugging Face", "Ollama", "ChromaDB", "FAISS", "Pinecone", "Qdrant",
     "Sentence Transformers", "LLM", "RAG", "A2A", "Agentic AI", "Prompt Engineering", "vLLM")
_reg("ml", "PyTorch", "PyTorch Lightning", "TensorFlow", "Keras", "scikit-learn", "XGBoost",
     "LightGBM", "OpenCV", "NLTK", "spaCy", "DVC", "MLflow", "Hydra", "Weights & Biases",
     "MLOps", "Deep Learning", "Machine Learning", "Neural Networks", "Computer Vision")
_reg("data", "Kafka", "PySpark", "Airflow", "Cassandra", "dbt", "Prefect", "Dagster",
     "DuckDB", "Polars", "pandas", "NumPy", "SciPy", "Matplotlib", "Seaborn", "Plotly",
     "Data Analysis", "Data Science", "BeautifulSoup", "Scrapy", "Selenium")
_reg("lang", "TypeScript", "JavaScript", "Python", "C++", "C", "Java", "Kotlin", "Swift",
     "Go", "Rust", "MATLAB", "HTML", "CSS", "SQL", "R", "Dart", "Node.js")
_reg("db", "PostgreSQL", "MongoDB", "Redis", "SQLite", "MySQL", "Firebase", "FaunaDB",
     "Prisma", "TypeORM", "Knex", "SQLAlchemy", "WatermelonDB", "Supabase")
_reg("ui", "styled-components", "Tailwind CSS", "Chakra UI", "Material UI", "Sass",
     "React Navigation", "Redux", "Zustand", "React Query", "React Hook Form", "Apollo",
     "GraphQL", "D3.js", "Chart.js", "ApexCharts", "Three.js", "Lottie", "Storybook")
_reg("infra", "Docker", "Kubernetes", "Helm", "Terraform", "GitHub Actions", "AWS", "GCP",
     "Netlify", "Vercel", "Socket.IO", "Stripe", "Prismic", "NextAuth", "JWT",
     "Netlify Identity", "MirageJS", "Axios", "Pydantic", "CMake", "Vite", "Webpack")
_reg("tool", "Jupyter", "Elasticsearch", "MinIO", "n8n", "Spark")
_reg("test", "Jest", "Vitest", "Cypress", "Testing Library", "pytest")

JS_DEPS = {
    "react-native": "React Native", "expo": "Expo", "next": "Next.js", "react": "React",
    "vue": "Vue", "nuxt": "Vue", "svelte": "Svelte", "@angular/core": "Angular",
    "express": "Express", "@nestjs/core": "NestJS", "fastify": "Fastify", "koa": "Koa",
    "electron": "Electron", "typescript": "TypeScript",
    "styled-components": "styled-components", "tailwindcss": "Tailwind CSS",
    "sass": "Sass", "node-sass": "Sass", "redux": "Redux", "@reduxjs/toolkit": "Redux",
    "zustand": "Zustand", "react-query": "React Query", "@tanstack/react-query": "React Query",
    "react-hook-form": "React Hook Form", "axios": "Axios", "graphql": "GraphQL",
    "firebase": "Firebase", "faunadb": "FaunaDB", "prisma": "Prisma", "@prisma/client": "Prisma",
    "typeorm": "TypeORM", "mongoose": "MongoDB", "mongodb": "MongoDB", "pg": "PostgreSQL",
    "mysql": "MySQL", "mysql2": "MySQL", "sqlite3": "SQLite", "knex": "Knex",
    "@supabase/supabase-js": "Supabase", "socket.io": "Socket.IO",
    "socket.io-client": "Socket.IO", "jest": "Jest", "vitest": "Vitest", "cypress": "Cypress",
    "vite": "Vite", "webpack": "Webpack", "stripe": "Stripe", "@stripe/stripe-js": "Stripe",
    "next-auth": "NextAuth", "jsonwebtoken": "JWT", "jwt-decode": "JWT",
    "netlify-identity-widget": "Netlify Identity", "miragejs": "MirageJS", "d3": "D3.js",
    "chart.js": "Chart.js", "apexcharts": "ApexCharts", "react-apexcharts": "ApexCharts",
    "three": "Three.js", "lottie-react-native": "Lottie", "lottie-react": "Lottie",
    "prismic-javascript": "Prismic", "openai": "OpenAI", "@anthropic-ai/sdk": "Anthropic",
    "langchain": "LangChain",
}
JS_PREFIXES = {
    "@react-navigation/": "React Navigation", "@chakra-ui/": "Chakra UI",
    "@mui/": "Material UI", "@material-ui/": "Material UI", "@storybook/": "Storybook",
    "@testing-library/": "Testing Library", "@apollo/": "Apollo",
    "@react-native-firebase/": "Firebase", "@prismicio/": "Prismic",
    "@nozbe/watermelondb": "WatermelonDB", "@langchain/": "LangChain", "expo-": "Expo",
}

# Python: package names (requirements) and import names, normalised to "-".
PY_DEPS = {
    "pandas": "pandas", "numpy": "NumPy", "scipy": "SciPy", "matplotlib": "Matplotlib",
    "seaborn": "Seaborn", "plotly": "Plotly", "sklearn": "scikit-learn",
    "scikit-learn": "scikit-learn", "tensorflow": "TensorFlow", "keras": "Keras",
    "torch": "PyTorch", "torchvision": "PyTorch", "pytorch-lightning": "PyTorch Lightning",
    "lightning": "PyTorch Lightning", "transformers": "Hugging Face",
    "datasets": "Hugging Face", "huggingface-hub": "Hugging Face", "xgboost": "XGBoost",
    "lightgbm": "LightGBM", "cv2": "OpenCV", "opencv-python": "OpenCV", "nltk": "NLTK",
    "spacy": "spaCy", "hydra": "Hydra", "hydra-core": "Hydra", "omegaconf": "Hydra",
    "dvc": "DVC", "mlflow": "MLflow", "wandb": "Weights & Biases", "fastapi": "FastAPI",
    "flask": "Flask", "django": "Django", "streamlit": "Streamlit", "gradio": "Gradio",
    "crewai": "CrewAI", "langgraph": "LangGraph", "openai": "OpenAI",
    "anthropic": "Anthropic", "mcp": "MCP", "fastmcp": "MCP", "llama-index": "LlamaIndex",
    "chromadb": "ChromaDB", "faiss": "FAISS", "faiss-cpu": "FAISS", "pinecone": "Pinecone",
    "pinecone-client": "Pinecone", "qdrant-client": "Qdrant", "ollama": "Ollama",
    "sentence-transformers": "Sentence Transformers", "vllm": "vLLM", "kafka": "Kafka",
    "kafka-python": "Kafka", "confluent-kafka": "Kafka", "aiokafka": "Kafka",
    "pyspark": "PySpark", "airflow": "Airflow", "apache-airflow": "Airflow",
    "cassandra": "Cassandra", "cassandra-driver": "Cassandra", "redis": "Redis",
    "psycopg2": "PostgreSQL", "psycopg2-binary": "PostgreSQL", "psycopg": "PostgreSQL",
    "asyncpg": "PostgreSQL", "pgvector": "PostgreSQL", "sqlalchemy": "SQLAlchemy",
    "pymongo": "MongoDB", "boto3": "AWS", "dbt-core": "dbt", "duckdb": "DuckDB",
    "polars": "Polars", "pydantic": "Pydantic", "pytest": "pytest", "bs4": "BeautifulSoup",
    "beautifulsoup4": "BeautifulSoup", "selenium": "Selenium", "scrapy": "Scrapy",
    "prefect": "Prefect", "dagster": "Dagster", "python-a2a": "A2A", "a2a": "A2A",
    "a2a-sdk": "A2A", "jupyter": "Jupyter", "notebook": "Jupyter",
}
PY_PREFIXES = {"langchain": "LangChain", "llama-index": "LlamaIndex",
               "google-cloud": "GCP", "dbt-": "dbt", "crewai": "CrewAI"}

# Repository topics that map onto known labels (everything else is title-cased).
TOPIC_ALIASES = {
    "llm": "LLM", "llms": "LLM", "rag": "RAG", "mcp-server": "MCP", "mcp": "MCP",
    "a2a-protocol": "A2A", "agentic-ai": "Agentic AI", "prompt-engineering": "Prompt Engineering",
    "langchain": "LangChain", "postgresql": "PostgreSQL", "redis": "Redis",
    "cassandra": "Cassandra", "docker": "Docker", "kafka": "Kafka", "pyspark": "PySpark",
    "airflow": "Airflow", "kubernetes": "Kubernetes", "python": "Python", "dvc": "DVC",
    "dvc-pipeline": "DVC", "gcp": "GCP", "hydra": "Hydra", "mlops": "MLOps",
    "machine-learning": "Machine Learning", "deep-learning": "Deep Learning",
    "deep-neural-networks": "Neural Networks", "neural-network": "Neural Networks",
    "torch": "PyTorch", "pytorch": "PyTorch", "tensorflow": "TensorFlow", "pandas": "pandas",
    "numpy": "NumPy", "matplotlib": "Matplotlib", "data-analysis": "Data Analysis",
    "data-science": "Data Science", "digital-image-processing": "Computer Vision",
    "computer-vision": "Computer Vision", "react": "React", "react-native": "React Native",
    "nextjs": "Next.js", "typescript": "TypeScript",
}
IGNORED_TOPICS = {"featured", "portfolio", "portfolio-hide", "dags", "dbeaver",
                  "supervised-learning"}

# Category scoring: every detected label adds its weight to the categories it belongs to.
CATEGORIES = {
    "AI & LLMs": {"LangChain": 3, "LangGraph": 3, "CrewAI": 3, "MCP": 3, "OpenAI": 2,
                  "Anthropic": 2, "LlamaIndex": 3, "Hugging Face": 2, "Ollama": 2,
                  "ChromaDB": 2, "FAISS": 2, "Pinecone": 2, "Qdrant": 2, "vLLM": 2,
                  "Sentence Transformers": 2, "LLM": 1, "RAG": 2, "A2A": 2,
                  "Agentic AI": 2, "Prompt Engineering": 1, "Gradio": 1},
    "Machine Learning": {"PyTorch": 2, "PyTorch Lightning": 2, "TensorFlow": 2, "Keras": 2,
                         "scikit-learn": 2, "XGBoost": 2, "LightGBM": 2, "DVC": 2,
                         "MLflow": 2, "Hydra": 1, "Weights & Biases": 1, "OpenCV": 2,
                         "MLOps": 2, "Deep Learning": 2, "Machine Learning": 2,
                         "Neural Networks": 2, "Computer Vision": 2, "NLTK": 1, "spaCy": 1},
    "Data Engineering": {"Kafka": 2, "Spark": 3, "PySpark": 3, "Airflow": 3, "Cassandra": 2, "dbt": 3,
                         "Kubernetes": 1, "Prefect": 3, "Dagster": 3, "DuckDB": 1},
    "Data Science": {"pandas": 1, "NumPy": 1, "Matplotlib": 1, "Seaborn": 1, "Plotly": 1,
                     "Jupyter": 1, "SciPy": 1, "Data Analysis": 2, "Data Science": 2},
    "Mobile": {"React Native": 4, "Expo": 3, "Flutter": 4, "React Navigation": 1},
    "Web": {"React": 2, "Next.js": 3, "Vue": 3, "Angular": 3, "Svelte": 3, "HTML": 1,
            "Tailwind CSS": 1, "Chakra UI": 1, "styled-components": 1, "Vite": 1},
    "Backend": {"Express": 3, "NestJS": 3, "Fastify": 3, "Koa": 3, "FastAPI": 2,
                "Flask": 2, "Django": 2, "Node.js": 1, "Prisma": 1, "TypeORM": 1},
    "Algorithms & CS": {"C": 2, "C++": 2, "MATLAB": 2, "CMake": 1},
}

# docker-compose image name fragments -> label
COMPOSE_IMAGES = {
    "postgres": "PostgreSQL", "pgvector": "PostgreSQL", "mysql": "MySQL", "mariadb": "MySQL",
    "mongo": "MongoDB", "redis": "Redis", "kafka": "Kafka", "cassandra": "Cassandra",
    "airflow": "Airflow", "elasticsearch": "Elasticsearch", "spark": "Spark",
    "minio": "MinIO", "dbt": "dbt", "n8n": "n8n", "ollama": "Ollama", "qdrant": "Qdrant",
    "chroma": "ChromaDB", "mlflow": "MLflow", "dagster": "Dagster", "prefect": "Prefect",
}

NOISE_LANGS = {"Shell", "Makefile", "Dockerfile", "Batchfile", "PowerShell", "Procfile",
               "Starlark", "Mako", "Jinja", "HCL"}
NATIVE_LANGS = {"Java", "Objective-C", "Objective-C++", "Ruby", "Kotlin", "Swift", "C++", "C"}
SKIP_DIRS = ("node_modules/", ".git/", "venv/", ".venv/", "env/", "__pycache__/",
             "site-packages/", "dist/", "build/", "Pods/", ".next/", ".expo/")


# --------------------------------------------------------------------------
# HTTP
# --------------------------------------------------------------------------

def _request(url: str, accept: str | None = None, auth: bool = True) -> bytes | None:
    headers = {"User-Agent": "portfolio-builder", "X-GitHub-Api-Version": "2022-11-28"}
    if accept:
        headers["Accept"] = accept
    if auth and TOKEN:
        headers["Authorization"] = f"Bearer {TOKEN}"
    for attempt in range(4):
        try:
            with urllib.request.urlopen(urllib.request.Request(url, headers=headers),
                                        timeout=30) as resp:
                return resp.read(4_000_000)
        except urllib.error.HTTPError as e:
            if e.code in (404, 409, 451):  # missing, empty repo, blocked
                return None
            if e.code in (403, 429) and e.headers.get("x-ratelimit-remaining") == "0":
                reset = int(e.headers.get("x-ratelimit-reset", "0"))
                sys.exit(f"GitHub rate limit hit (resets {datetime.fromtimestamp(reset)}). "
                         "Set GITHUB_TOKEN to raise the limit.")
            if attempt == 3:
                raise
        except (urllib.error.URLError, TimeoutError):
            if attempt == 3:
                raise
        time.sleep(1.5 * (attempt + 1))
    return None


def api(path: str, accept: str = "application/vnd.github+json"):
    data = _request(f"{API}/{path.lstrip('/')}", accept)
    if data is None:
        return None
    return json.loads(data) if "json" in accept else data.decode("utf-8", "replace")


def api_all(path: str) -> list:
    items, page = [], 1
    sep = "&" if "?" in path else "?"
    while True:
        batch = api(f"{path}{sep}per_page=100&page={page}") or []
        items += batch
        if len(batch) < 100:
            return items
        page += 1


def raw(owner: str, repo: str, branch: str, path: str) -> str | None:
    url = f"{RAW}/{owner}/{repo}/{branch}/{urllib.parse.quote(path)}"
    data = _request(url, auth=False)
    return data.decode("utf-8", "replace") if data is not None else None


# --------------------------------------------------------------------------
# Stack detection
# --------------------------------------------------------------------------

def _norm(name: str) -> str:
    return name.strip().lower().replace("_", "-")


def _py_label(name: str) -> str | None:
    n = _norm(name)
    if n in PY_DEPS:
        return PY_DEPS[n]
    for prefix, label in PY_PREFIXES.items():
        if n.startswith(prefix):
            return label
    return None


def _js_label(name: str) -> str | None:
    if name in JS_DEPS:
        return JS_DEPS[name]
    for prefix, label in JS_PREFIXES.items():
        if name.startswith(prefix):
            return label
    return None


IMPORT_RE = re.compile(r"^\s*(?:from\s+([A-Za-z_]\w*)[\w.]*\s+import|import\s+([A-Za-z_]\w*))",
                       re.M)


def python_imports(source: str) -> set[str]:
    return {a or b for a, b in IMPORT_RE.findall(source)}


def notebook_source(text: str) -> str:
    try:
        nb = json.loads(text)
    except json.JSONDecodeError:
        return ""
    cells = nb.get("cells") or nb.get("worksheets", [{}])[0].get("cells", [])
    out = []
    for cell in cells:
        if cell.get("cell_type") == "code":
            src = cell.get("source") or cell.get("input") or ""
            out.append("".join(src) if isinstance(src, list) else src)
    return "\n".join(out)


def _depth(path: str) -> int:
    return path.count("/")


def detect_stack(owner: str, name: str, branch: str, paths: list[str],
                 languages: dict[str, int], topics: list[str]) -> tuple[list[str], dict]:
    """Return (ordered stack labels, facts used for README drafts)."""
    found: set[str] = set()
    facts: dict = {"scripts": {}, "package_manager": None, "python_reqs": None,
                   "has_notebooks": False, "has_compose": False, "dirs": []}
    lower = [p.lower() for p in paths]
    base = {posixpath.basename(p) for p in lower}

    # --- files ---------------------------------------------------------------
    if "dockerfile" in base or any(b.startswith("dockerfile") for b in base):
        found.add("Docker")
    if base & {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}:
        found.add("Docker")
        facts["has_compose"] = True
    if "dvc.yaml" in base or any(p.endswith(".dvc") for p in lower):
        found.add("DVC")
    if any(p.endswith(".ipynb") for p in lower):
        found.add("Jupyter")
        facts["has_notebooks"] = True
    if any(p.startswith("dags/") or "/dags/" in p for p in lower):
        found.add("Airflow")
    if "chart.yaml" in base:
        found.update({"Helm", "Kubernetes"})
    if any(re.search(r"(^|/)(k8s|kubernetes|manifests)/", p) for p in lower):
        found.add("Kubernetes")
    if any(p.endswith(".tf") for p in lower):
        found.add("Terraform")
    if any(p.startswith(".github/workflows/") for p in lower):
        found.add("GitHub Actions")
    if "cmakelists.txt" in base:
        found.add("CMake")
    if "netlify.toml" in base:
        found.add("Netlify")
    if "vercel.json" in base:
        found.add("Vercel")
    if "schema.prisma" in base:
        found.add("Prisma")
    if "tsconfig.json" in base:
        found.add("TypeScript")
    if any(b.startswith("tailwind.config") for b in base):
        found.add("Tailwind CSS")
    if any(b.startswith("next.config") for b in base):
        found.add("Next.js")
    if "pubspec.yaml" in base:
        found.update({"Flutter", "Dart"})
    if any(p.endswith(".sql") for p in lower):
        found.add("SQL")
    if "yarn.lock" in base:
        facts["package_manager"] = "yarn"
    elif "pnpm-lock.yaml" in base:
        facts["package_manager"] = "pnpm"

    facts["dirs"] = sorted({p.split("/")[0] for p in paths if "/" in p
                            and not p.startswith(".")})[:12]

    # --- manifests -----------------------------------------------------------
    by_depth = sorted(paths, key=_depth)
    pkg_files = [p for p in by_depth if posixpath.basename(p) == "package.json"][:3]
    for i, p in enumerate(pkg_files):
        text = raw(owner, name, branch, p)
        try:
            pkg = json.loads(text) if text else {}
        except json.JSONDecodeError:
            pkg = {}
        deps = {**pkg.get("dependencies", {}), **pkg.get("devDependencies", {})}
        for dep in deps:
            if label := _js_label(dep):
                found.add(label)
        if i == 0:
            facts["scripts"] = pkg.get("scripts", {}) or {}
            facts["package_manager"] = facts["package_manager"] or "npm"
        if deps and not ({"react", "next", "vue", "svelte", "@angular/core", "react-native"}
                         & set(deps)):
            found.add("Node.js")

    req_files = [p for p in by_depth if re.fullmatch(r"requirements[\w.-]*\.txt",
                                                     posixpath.basename(p).lower())][:3]
    for p in req_files:
        text = raw(owner, name, branch, p) or ""
        facts["python_reqs"] = facts["python_reqs"] or p
        for line in text.splitlines():
            line = line.split("#")[0].strip()
            if not line or line.startswith("-"):
                continue
            pkg_name = re.split(r"[<>=!~\[;@ ]", line, maxsplit=1)[0]
            if label := _py_label(pkg_name):
                found.add(label)

    other_manifests = [p for p in by_depth if posixpath.basename(p).lower() in
                       {"pyproject.toml", "pipfile", "environment.yml", "environment.yaml",
                        "setup.py", "setup.cfg"}][:3]
    for p in other_manifests:
        text = raw(owner, name, branch, p) or ""
        facts["python_reqs"] = facts["python_reqs"] or p
        for word in set(re.findall(r"[A-Za-z][A-Za-z0-9_.\-]*", text)):
            if label := _py_label(word):
                found.add(label)

    compose = [p for p in by_depth if posixpath.basename(p).lower() in
               {"docker-compose.yml", "docker-compose.yaml", "compose.yml", "compose.yaml"}][:2]
    for p in compose:
        text = raw(owner, name, branch, p) or ""
        for image in re.findall(r"^\s*image:\s*['\"]?([^\s'\"]+)", text, re.M):
            img = image.lower().split(":")[0]
            for frag, label in COMPOSE_IMAGES.items():
                if frag in img:
                    found.add(label)

    # --- python sources (catches repos without a requirements file) ----------
    py_sources = [p for p in by_depth if p.endswith((".py", ".ipynb"))][:8]
    for p in py_sources:
        text = raw(owner, name, branch, p) or ""
        if p.endswith(".ipynb"):
            text = notebook_source(text)
        for mod in python_imports(text):
            if label := _py_label(mod):
                found.add(label)

    # --- topics --------------------------------------------------------------
    for t in topics:
        if t in IGNORED_TOPICS:
            continue
        found.add(TOPIC_ALIASES.get(t) or t.replace("-", " ").title())

    # --- languages -----------------------------------------------------------
    total = sum(languages.values()) or 1
    mobile = bool({"React Native", "Flutter"} & found)
    for lang, size in languages.items():
        if lang in NOISE_LANGS or (mobile and lang in NATIVE_LANGS):
            continue
        if size / total < 0.08:
            continue
        if lang == "Jupyter Notebook":
            found.update({"Jupyter", "Python"})
        elif lang in ("CSS", "HTML", "SCSS") and len(found) > 2:
            continue
        else:
            found.add("Sass" if lang == "SCSS" else lang)
    if "TypeScript" in found:
        found.discard("JavaScript")
    if mobile:
        found.discard("CMake")  # native build files of React Native / Flutter
    if "PySpark" in found:
        found.discard("Spark")
    if {"Next.js", "React Native"} & found:
        found.discard("React")  # implied by the framework

    def order(label: str) -> tuple[int, str]:
        group = LABELS.get(label, "tool")
        return (GROUP_ORDER.index(group), label.lower())

    return sorted(found, key=order), facts


def pick_category(stack: list[str], name: str, primary_lang: str | None) -> str:
    lname = name.lower()
    if any(k in lname for k in ("leetcode", "algorithm", "grafos", "graph", "oop")):
        return "Algorithms & CS"
    scores = {cat: sum(w.get(label, 0) for label in stack) for cat, w in CATEGORIES.items()}
    tokens = set(re.split(r"[^a-z0-9]+", lname))
    if tokens & {"elt", "etl", "pipeline", "streaming", "airflow", "kafka", "spark", "dbt"}:
        scores["Data Engineering"] += 3
    if tokens & {"rag", "llm", "agent", "agents", "mcp", "crewai", "langchain"}:
        scores["AI & LLMs"] += 3
    best = max(scores, key=lambda c: scores[c])
    if scores[best] > 0:
        return best
    fallback = {"C": "Algorithms & CS", "C++": "Algorithms & CS", "MATLAB": "Algorithms & CS",
                "Jupyter Notebook": "Data Science", "TypeScript": "Web",
                "JavaScript": "Web", "HTML": "Web", "Python": "Python"}
    return fallback.get(primary_lang or "", "Other")


# --------------------------------------------------------------------------
# README handling
# --------------------------------------------------------------------------

class _ParagraphParser(HTMLParser):
    """Collect text of <p> elements, tracking how much of it is link text."""

    def __init__(self) -> None:
        super().__init__()
        self.paragraphs: list[tuple[str, int]] = []
        self.images: list[dict] = []
        self._in_p = 0
        self._in_a = 0
        self._buf: list[str] = []
        self._link_chars = 0

    def handle_starttag(self, tag, attrs):
        a = dict(attrs)
        if tag == "p":
            self._in_p += 1
            self._buf, self._link_chars = [], 0
        elif tag == "a":
            self._in_a += 1
        elif tag == "img":
            self.images.append(a)

    def handle_endtag(self, tag):
        if tag == "p" and self._in_p:
            self._in_p -= 1
            text = re.sub(r"\s+", " ", "".join(self._buf)).strip()
            if text:
                self.paragraphs.append((text, self._link_chars))
        elif tag == "a" and self._in_a:
            self._in_a -= 1

    def handle_data(self, data):
        if self._in_p:
            self._buf.append(data)
            if self._in_a:
                self._link_chars += len(data.strip())


BADGE_HINTS = ("shields.io", "badge", "badgen", "travis-ci", "codecov", "github/workflow",
               "forthebadge", "skillicons", "devicon", "simpleicons", "readme-typing")


def readme_summary(parser: _ParagraphParser) -> str | None:
    for text, link_chars in parser.paragraphs:
        if len(text) < 40 or link_chars > 0.5 * len(text):
            continue
        if text.count("•") >= 2 or text.count("|") >= 2:
            continue
        if text.rstrip().endswith(":"):  # "To get started, follow these steps:" introduces a list
            continue
        return text if len(text) <= 240 else text[:237].rsplit(" ", 1)[0] + "…"
    return None


def readme_cover(parser: _ParagraphParser, base_raw: str, readme_dir: str) -> str | None:
    for img in parser.images:
        src = img.get("data-canonical-src") or img.get("src") or ""
        low = src.lower()
        if not src or any(h in low for h in BADGE_HINTS) or low.endswith((".svg", ".ico")):
            continue
        try:
            if int(str(img.get("width", "999")).rstrip("px")) < 120:
                continue
        except ValueError:
            pass
        return _absolute(img.get("src") or src, base_raw, readme_dir)
    return None


def _absolute(url: str, base: str, readme_dir: str) -> str:
    if re.match(r"^(https?:|mailto:|data:|#)", url):
        return url
    path = url.lstrip("/") if url.startswith("/") else posixpath.join(readme_dir, url)
    path = posixpath.normpath(path)
    return f"{base}/{path}"


ANCHOR_RE = re.compile(r'<a id="user-content-[^"]*" class="anchor"[^>]*>.*?</a>', re.S)
ATTR_RE = re.compile(r'\b(src|href|srcset)="([^"]*)"')


def clean_readme_html(html: str, owner: str, name: str, branch: str, readme_path: str) -> str:
    html = ANCHOR_RE.sub("", html)
    readme_dir = posixpath.dirname(readme_path)
    raw_base = f"{RAW}/{owner}/{name}/{branch}"
    blob_base = f"https://github.com/{owner}/{name}/blob/{branch}"

    def fix(m: re.Match) -> str:
        attr, val = m.group(1), m.group(2)
        if attr == "srcset":
            parts = [p.strip().split(" ", 1) for p in val.split(",") if p.strip()]
            val = ", ".join(" ".join([_absolute(p[0], raw_base, readme_dir), *p[1:]])
                            for p in parts)
        elif attr == "src":
            val = _absolute(val, raw_base, readme_dir)
        else:
            val = _absolute(val, blob_base, readme_dir)
        return f'{attr}="{val}"'

    html = ATTR_RE.sub(fix, html)
    # Open external links in a new tab.
    return re.sub(r'<a (?![^>]*target=)([^>]*href="https?:)', r'<a target="_blank" rel="noopener" \1',
                  html)


# --------------------------------------------------------------------------
# Generated text for repos without a README
# --------------------------------------------------------------------------

KIND = {
    "AI & LLMs": "AI application", "Machine Learning": "machine learning project",
    "Data Engineering": "data pipeline", "Data Science": "data analysis project",
    "Mobile": "mobile app", "Web": "web application", "Backend": "backend API",
    "Algorithms & CS": "program", "Python": "Python project", "Other": "project",
}


def humanize(name: str) -> str:
    words = re.sub(r"[-_]+", " ", name).strip()
    words = re.sub(r"(?<=[a-z])(?=[A-Z])", " ", words)
    return re.sub(r"\s+", " ", words).strip() or name


def _join(items: list[str]) -> str:
    return items[0] if len(items) == 1 else ", ".join(items[:-1]) + " and " + items[-1]


STRONG_DATA = {"Kafka", "PySpark", "Spark", "Airflow", "dbt", "Cassandra", "Prefect", "Dagster"}


def generated_summary(name: str, category: str, stack: list[str]) -> str:
    kind = KIND.get(category, "project")
    leads = [s for s in stack if LABELS.get(s) in ("framework", "ai", "ml") or s in STRONG_DATA]
    if not leads:
        leads = [s for s in stack if LABELS.get(s) == "lang" and s.lower() not in kind.lower()]
    lead = leads[0] if leads else None
    rest = [s for s in stack if s != lead and LABELS.get(s) != "test"
            and s.lower() not in kind.lower()][:3]
    text = f"{_article(lead)} {lead} {kind}" if lead else f"{_article(kind)} {kind}"
    if rest:
        text += f" built with {_join(rest)}"
    text += "."
    lname = name.lower()
    if "ignite" in lname:
        text += " Developed during Rocketseat's Ignite bootcamp."
    elif "nlw" in lname:
        text += " Developed during Rocketseat's Next Level Week."
    elif "challenge" in lname or "desafio" in lname:
        text += " Built as a coding challenge."
    return text


def _article(word: str) -> str:
    if word.isupper() and word not in ("MATLAB",):  # acronyms: "an HTML", "an MCP"
        return "An" if word[0] in "AEFHILMNORSX" else "A"
    return "An" if word[:1].lower() in "aeiou" else "A"


def readme_draft(p: dict, facts: dict) -> str:
    intro = p["summary"]
    if p["summary_source"] != "generated":
        intro += "\n\n" + generated_summary(p["name"], p["category"], p["stack"])
    lines = [f"# {p['title']}", "", intro, "", "## Tech stack", ""]
    lines += [f"- {s}" for s in p["stack"]] or ["- (not detected)"]
    lines += ["", "## Getting started", "", "```bash",
              f"git clone {p['url']}.git", f"cd {p['name']}"]
    pm = facts.get("package_manager")
    scripts = facts.get("scripts") or {}
    if pm:
        lines.append("yarn" if pm == "yarn" else f"{pm} install")
        for script in ("dev", "start", "android", "ios", "test"):
            if script in scripts:
                lines.append(f"{pm} run {script}" if pm != "yarn" else f"yarn {script}")
                if script in ("dev", "start"):
                    break
    if facts.get("python_reqs", "") and facts["python_reqs"].endswith(".txt"):
        lines += ["python -m venv .venv && source .venv/bin/activate",
                  f"pip install -r {facts['python_reqs']}"]
    elif facts.get("python_reqs"):
        lines.append("pip install -e .")
    if facts.get("has_compose"):
        lines.append("docker compose up")
    if facts.get("has_notebooks"):
        lines.append("jupyter notebook")
    if "C++" in p["stack"] or "C" in p["stack"]:
        lines.append("# compile the sources with your C/C++ compiler, e.g. g++ -O2 *.cpp -o app")
    lines.append("```")
    if facts.get("dirs"):
        lines += ["", "## Project structure", "", "```"]
        lines += [f"{d}/" for d in facts["dirs"]]
        lines.append("```")
    lines += ["", "---", "", f"_Part of [{p['owner']}'s portfolio](https://{p['owner']}.github.io)._", ""]
    return "\n".join(lines)


# --------------------------------------------------------------------------
# Build
# --------------------------------------------------------------------------

def load_config() -> dict:
    cfg = json.loads(CONFIG_PATH.read_text()) if CONFIG_PATH.exists() else {}
    cfg.setdefault("username", os.environ.get("GITHUB_REPOSITORY_OWNER", ""))
    if not cfg["username"]:
        sys.exit("Set 'username' in portfolio.config.json")
    return cfg


def process_repo(owner: str, repo: dict, featured: list[str]) -> tuple[dict, dict, str | None]:
    name, branch = repo["name"], repo["default_branch"]
    languages = api(f"repos/{owner}/{name}/languages") or {}
    tree = api(f"repos/{owner}/{name}/git/trees/{urllib.parse.quote(branch)}?recursive=1") or {}
    paths = [t["path"] for t in tree.get("tree", []) if t.get("type") == "blob"
             and not any(f"/{d}" in f"/{t['path']}" for d in SKIP_DIRS)]
    topics = repo.get("topics", [])
    stack, facts = detect_stack(owner, name, branch, paths, languages, topics)
    category = pick_category(stack, name, repo.get("language"))

    readme_meta = api(f"repos/{owner}/{name}/readme")
    readme_html = summary_from_readme = cover = None
    if readme_meta:
        html = api(f"repos/{owner}/{name}/readme", "application/vnd.github.html")
        if html:
            parser = _ParagraphParser()
            parser.feed(html)
            summary_from_readme = readme_summary(parser)
            readme_dir = posixpath.dirname(readme_meta["path"])
            cover = readme_cover(parser, f"{RAW}/{owner}/{name}/{branch}", readme_dir)
            readme_html = clean_readme_html(html, owner, name, branch, readme_meta["path"])

    description = (repo.get("description") or "").strip()
    if _norm(description) == _norm(name):  # description that just repeats the name
        description = ""
    if description and (len(description) >= 45 or not summary_from_readme):
        summary, source = description, "description"
    elif summary_from_readme:
        summary, source = summary_from_readme, "readme"
    else:
        summary, source = generated_summary(name, category, stack), "generated"

    total = sum(languages.values()) or 1
    langs = [{"name": k, "pct": round(v * 100 / total, 1)}
             for k, v in sorted(languages.items(), key=lambda kv: -kv[1])
             if v / total >= 0.01][:5]

    project = {
        "name": name,
        "owner": owner,
        "title": humanize(name),
        "url": repo["html_url"],
        "homepage": (repo.get("homepage") or "").strip() or None,
        "summary": summary,
        "summary_source": source,
        "category": category,
        "stack": stack,
        "languages": langs,
        "topics": topics,
        "stars": repo["stargazers_count"],
        "forks": repo["forks_count"],
        "created": repo["created_at"],
        "updated": repo["pushed_at"],
        "archived": repo.get("archived", False),
        "featured": name in featured or "featured" in topics,
        "cover": cover,
        "has_readme": bool(readme_meta),
        "readme": f"readmes/{name}.html" if readme_html else None,
    }
    if project["homepage"] and not project["homepage"].startswith("http"):
        project["homepage"] = "https://" + project["homepage"]
    return project, facts, readme_html


def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawTextHelpFormatter)
    ap.add_argument("--readme-drafts", action="store_true",
                    help="write README drafts for repos without one to readme-drafts/")
    ap.add_argument("--only", nargs="*", help="process only these repos (debugging)")
    args = ap.parse_args()

    if not TOKEN:
        print("warning: no GITHUB_TOKEN set; unauthenticated limit is 60 requests/hour",
              file=sys.stderr)

    cfg = load_config()
    owner = cfg["username"]
    exclude = set(cfg.get("exclude", [])) | {owner, f"{owner}.github.io"}
    featured = cfg.get("featured", [])

    user = api(f"users/{owner}") or {}
    repos = [r for r in api_all(f"users/{owner}/repos?type=owner&sort=pushed")
             if r["name"] not in exclude
             and (cfg.get("include_forks") or not r["fork"])
             and (cfg.get("include_archived", True) or not r.get("archived"))
             and "portfolio-hide" not in r.get("topics", [])]
    if args.only:
        repos = [r for r in repos if r["name"] in args.only]
    print(f"Processing {len(repos)} repositories for {owner}…")

    with ThreadPoolExecutor(max_workers=8) as pool:
        results = list(pool.map(lambda r: process_repo(owner, r, featured), repos))

    # Output dir
    if OUT.exists():
        shutil.rmtree(OUT)
    shutil.copytree(SITE_SRC, OUT)
    (OUT / "data").mkdir()
    (OUT / "readmes").mkdir()

    projects = []
    for project, facts, readme_html in results:
        projects.append(project)
        if readme_html:
            (OUT / "readmes" / f"{project['name']}.html").write_text(readme_html)

    rank = {n: i for i, n in enumerate(featured)}
    projects.sort(key=lambda p: (not p["featured"], rank.get(p["name"], 999),
                                 -datetime.fromisoformat(p["updated"].replace("Z", "+00:00"))
                                 .timestamp()))

    profile = {
        "username": owner,
        "name": cfg.get("name") or user.get("name") or owner,
        "headline": cfg.get("headline") or user.get("bio") or "",
        "tagline": cfg.get("tagline", ""),
        "about": cfg.get("about", []),
        "avatar": user.get("avatar_url"),
        "location": user.get("location"),
        "github": user.get("html_url") or f"https://github.com/{owner}",
        "links": cfg.get("links", []),
    }
    data = {
        "generated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "profile": profile,
        "projects": projects,
    }
    (OUT / "data" / "projects.json").write_text(json.dumps(data, ensure_ascii=False, indent=1))

    if args.readme_drafts:
        if DRAFTS.exists():
            shutil.rmtree(DRAFTS)
        for project, facts, _ in results:
            if not project["has_readme"]:
                d = DRAFTS / project["name"]
                d.mkdir(parents=True)
                (d / "README.md").write_text(readme_draft(project, facts))

    counts = {}
    for p in projects:
        counts[p["summary_source"]] = counts.get(p["summary_source"], 0) + 1
    print(f"Wrote {len(projects)} projects to {OUT.relative_to(ROOT)}/ "
          f"(summaries: {', '.join(f'{v} {k}' for k, v in counts.items())})")
    if args.readme_drafts:
        n = sum(1 for p in projects if not p["has_readme"])
        print(f"Wrote {n} README drafts to {DRAFTS.relative_to(ROOT)}/")


if __name__ == "__main__":
    main()
