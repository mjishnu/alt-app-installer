import logging

from maingui import main

logging.basicConfig(filename='log.txt',
                    filemode='a',
                    format='%(asctime)s.%(msecs)03d %(levelname)s: %(message)s',
                    datefmt='%d-%m-%Y %H:%M:%S',
                    level=logging.INFO)

logging.info("Running App Installer")

logger = logging.getLogger('urbanGUI')

try:
    main()
except Exception as e:
    print(e, ', check full log in logs.txt')
    logging.error(e, exc_info=True)

logging.info("Run Completed!")
logging.info(" ")
