#!/usr/bin/env python3
import socket
import ollama
import requests


def GPTJ(msg, ip="165.93.125.232", port=5050):
    """!
    Sends a message to a GPT-J server and retrieves the response.

    @param msg<str>: The message to send to the server.
    @param ip<str>: The IP address of the GPT-J server. Default is "165.93.125.232".
    @param port<int>: The port on which the GPT-J server is listening. Default is 5050.
    @return str: The server's response, or "Server not reachable" if the connection fails.
    """
    try:
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
        server_address = (ip, port)
        client_socket.connect(server_address)
        myHist = []
        message = msg  ## Message to be sent to the server
        if message == "exit":
            client_socket.close()

        client_socket.sendall(message.encode())  ## Send the message to the server

        message = client_socket.recv(2048)  ## Receive the response from the server
        if not message:
            pass
        else:
            message = message.decode("utf-8")
            myHist = myHist[:10] + [message]
            return message
    except:
        return "Server not reachable"


def ollama_local(msg, model="llama3"):
    """!
    Sends a message to a local instance of the Ollama model and retrieves the response.

    @param msg<str>: The message to send to the model.
    @param model<str>: The name of the model to use. Default is "llama3".
    @return str: The model's response to the message.
    """
    response = ollama.chat(
        model=model,
        messages=[
            {
                "role": "user",
                "content": msg,
            },
        ],
    )
    return response["message"]["content"]


def ollama_server(msg, model="llama3", IP="localhost", port=11434):
    """!
    Sends a message to a remote Ollama server and retrieves the response.

    @param msg<str>: The message to send to the server.
    @param model<str>: The name of the model to use. Default is "llama3".
    @param IP<str>: The IP address of the Ollama server. Default is "localhost".
    @param port<int>: The port on which the Ollama server is listening. Default is 11434.
    @return str: The server's response to the message in JSON format.
    """
    json_data = {
        'model': model,
        'messages': [{'role': "user", 'content': msg}],
        'stream': False
    }
    response = requests.post(f'http://{IP}:{port}/api/chat', json=json_data)
    return response.text