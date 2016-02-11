FROM library/python:3-onbuild

EXPOSE 5000

CMD [ "python", "dash.py" ]
