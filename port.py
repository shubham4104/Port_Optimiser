class Port:
    port_width = 10

    def __init__(self, port_id, length, block_id=""):
        # Initialize the port with id, length, and optional block id.
        self.port_id = port_id
        self.length = length
        self.block_id = block_id

    def get_port_length(self):
        # Get the length of the port.
        return self.length

    def get_port_block(self):
        # Get the block ID of the port.
        return self.block_id

    def get_port_id(self):
        # Get the port ID.
        return self.port_id

    def set_port_id(self, port_id):
        # Set the port ID. """
        self.port_id = port_id

    def set_port_block(self, block_id):
        # Set the block ID for the port.
        self.block_id = block_id

    def __str__(self):
        # String representation of the port.
        return f"{self.block_id} {self.port_id} {self.length}"

    def get_key(self):
        # Generate a key representing the port.
        return f"{self.block_id} {self.port_id} {self.length}"
