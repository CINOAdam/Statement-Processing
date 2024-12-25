# coding=utf-8
import os
import sys
from os.path import abspath, dirname
from inspect import stack
import logging



__author__ = "Adam Kruger"

sys.dont_write_bytecode = True
path_app = dirname(abspath(stack()[0][1]))

if path_app not in sys.path:
    sys.path.append(path_app)

path_source = os.path.dirname(os.path.abspath(__file__))

def load_env_file(filepath):
    print(f"Loading environment from {filepath}...")
    try:
        with open(filepath) as f:
            for line in f:
                if line.strip() and not line.startswith("#"):
                    key, value = line.strip().split("=", 1)
                    os.environ[key] = value
        print("Environment loaded successfully")
    except FileNotFoundError:
        print(
            f"Environment file {filepath} not found. Checking system environment variables."
        )
        logging.warning(
            f"Environment file {filepath} not found. Checking system environment variables."
        )
    except Exception as e:
        print(f"Error loading environment file: {e}")
        logging.error(f"Error loading environment file: {e}")


# Load environment variables from .env file
load_env_file(".env")

# Configure OpenAI
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
if not OPENAI_API_KEY:
    raise ValueError(
        "OPENAI_API_KEY environment variable is not set. Please set it in .env file or system environment."
    )
