# Shokudou API

This is the Shokudou API that collates data from the ESP32s and provides them to users. It is written in Flask and uses a SQLite database for portability.

We recommend running this using ``gunicorn`` with an ``nginx`` backend. Due to the use of global variables, **running the API with multiple threads is currently not possible**.

A ``config.py`` file must be placed in the same directory as ``app.py`` with the following variables:
```python
NUM_DETECTORS = number of ESP32s
NUM_STALLS = NUM_DETECTORS # for future use
SECRET = '<API Secret>'
```

``model.py`` is used to process the data. The data processing step is run with ``Flask-Executor`` in case of long-running models or processing.

Dependencies can be installed by running ``pip install requirements.txt``.