# openLCA Python Tutorial
This tutorial explains the usage of the openLCA API from Python ... 


## Content
* ...
* [Setting up a development environment](./ide_setup.md)


## Hello world!
Open the openLCA Python editor under `Window > Developer tools > Python` and
execute the following script: 

```python
from org.openlca.app.util import UI, Dialog
from org.openlca.app import App

def say_hello():
    Dialog.showInfo(UI.shell(), 'Hello from Python (Jython)!')

if __name__ == '__main__':
    App.runInUI('say hello', say_hello)
```


## License
This project is in the worldwide public domain, released under the 
[CC0 1.0 Universal Public Domain Dedication](https://creativecommons.org/publicdomain/zero/1.0/).

![Public Domain Dedication](https://licensebuttons.net/p/zero/1.0/88x31.png) 
