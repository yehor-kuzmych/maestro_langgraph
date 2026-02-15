#!/usr/bin/env python3
import rclpy
import os
from rclpy.node import Node
from rooted_msgs.srv import MemoryRequest

import sqlite3 as sql
from queue import Queue
import threading
from rcl_interfaces.msg import ParameterDescriptor

insert_queue = Queue()
database_folder = "."


def create_table(conn, create_table_sql):
    """!
    Creates a table in the database using the provided SQL statement.

    @param conn<sqlite3.Connection>: The database connection object.
    @param create_table_sql<str>: A SQL statement for creating the table.
    """
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
    except Exception as e:
        print(e)


class MemoryServer(Node):
    """!
    A ROS2 Node that provides a service for interacting with SQLite databases.
    """

    def __init__(self):
        """!
        Constructor for the MemoryServer class. Initializes the ROS2 service and database parameters.
        """
        super().__init__("memory_server")
        self.srv = self.create_service(MemoryRequest, "memory_service", self.handle_request)

        folder_descriptor = ParameterDescriptor(description='Path of the folder which contains all database files.')
        self.declare_parameter('db_folder_path', '', folder_descriptor)

        self.database_folder = self.get_parameter('db_folder_path').value

        global database_folder
        database_folder = self.database_folder

    def handle_request(self, req, resp):
        """!
        Handles incoming database commands from the service client.

        @param req<MemoryRequest.Request>: The service request containing the database name and command.
        @param resp<MemoryRequest.Response>: The service response containing the result of the operation.
        @return<MemoryRequest.Response>: The response populated with the operation result.
        """
        database_name = req.db_name
        command = req.command
        response = None
        db, cursor = None, None

        if "SELECT" in command or "INSERT" in command:
            try:
                assert os.path.isfile(f"{self.database_folder}/{database_name}")
            except AssertionError:
                self.get_logger().error(f"{database_name} could not be found in {self.database_folder}")
                response = "Failed"

            try:
                db = sql.connect(f"{self.database_folder}/{database_name}")
                cursor = db.cursor()
            except:
                self.get_logger().error(f"There was a problem connecting to {database_name}.")
                response = "Failed"

            if "INSERT" in command:
                global insert_queue
                insert_queue.put([database_name, command])
                response = "Success"

            elif "SELECT" in command:
                cursor.execute(command)
                response = str([i[0] for i in cursor.fetchall()])
            else:
                response = "Success"
            resp.result = response

        else:
            self.get_logger().error(f"Command does not read or write from/in database {database_name}.")
            response = "Failed"

        return resp


class MemoryWriter:
    """!
    A background worker that processes database insertion commands from a queue.
    """

    def __init__(self):
        """!
        Constructor for the MemoryWriter class. Starts the insertion process.
        """
        self.main_routine()

    def main_routine(self):
        """!
        Main routine for handling insertion operations from the queue.
        """
        global insert_queue
        global database_folder
        while True:
            while not insert_queue.empty():
                current_insertion = insert_queue.get()
                db_name = current_insertion[0]
                command = current_insertion[1]
                try:
                    # Open the database connection
                    db = sql.connect(f"{database_folder}/{db_name}")
                    cursor = db.cursor()
                    # Execute the command
                    cursor.execute(command)
                    # Commit the transaction
                    db.commit()
                except Exception as e:
                    print("Failed to perform insertion operation due to:", e)
                finally:
                    # Ensure the database is closed properly
                    if db:
                        db.close()


def memory_server_start():
    """!
    Starts the MemoryServer node.
    """
    memory_manager = MemoryServer()
    rclpy.spin(memory_manager)


def memory_writer_start():
    """!
    Starts the MemoryWriter worker.
    """
    writer = MemoryWriter()
    writer


def main():
    """!
    Entry point for the memory server application. Initializes and starts threads for both the server and the writer.
    """
    writer_thread = threading.Thread(target=memory_writer_start, args=())
    writer_thread.start()
    rclpy.init(args=None)
    memory_server_start()
    rclpy.shutdown()


if __name__ == "__main__":
    main()
