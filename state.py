import math
from copy import copy, deepcopy
from block_ip import BlockIP

class state:
    # Class variables for shared resources
    block_list = []
    map_blocks = {}
    map_connectivity = {}
    action_set = []

    def __init__(self, blocks):
        # Initialize a new state instance
        self.blocks = copy(blocks)
        self.visits = 0
        self.cost = 0.0
        self.children = []  # Child nodes for this state
        self.parent = None  # Parent of this state
        self.unexplored = []  # Unexplored actions
        self.count_child = 0  # Number of child nodes
        self.eps = 30  # Exploration parameter
        self.penalty = 0  # Penalty for overlap
        self.level = 0  # Depth level in the MCTS tree
        self.init_unexplored()

    @classmethod
    def initialise_class(cls, block_list, map_blocks, map_connectivity, action_set):
        # Class method to initialize class variables
        cls.block_list = block_list
        cls.map_blocks = map_blocks
        cls.map_connectivity = map_connectivity
        cls.action_set = action_set

    def init_unexplored(self):
        # Initialize unexplored actions for the state
        self.unexplored = list(range(len(state.action_set)))

    def add_child(self, child):
        # Add a child state
        self.children.append(child)
        self.count_child += 1

    def get_key(self):
        # Generate a unique key for the state
        key = ""
        for block in self.blocks:
            key += block.get_key()
        return key

    def best_child_traverse(self):
        # Choose the best child for traversal based on some metric
        value = -1e12
        pos = 0
        for index, child in enumerate(self.children):
            curr_value = child.get_state_traverse_value()
            if curr_value > value:
                value = curr_value
                pos = index 
        return self.children[pos]

    def best_child(self):
        # Choose the best child based on state value
        value = -1e12
        pos = 0
        for index, child in enumerate(self.children):
            curr_value = child.get_state_value()
            if curr_value > value:
                value = curr_value
                pos = index 
        return self.children[pos]
    
    def get_state_traverse_value(self):
        # Calculate state value for traversal
        global global_t
        curr_visits = self.visits if self.visits > 0 else 0.0000000001
        return -(self.cost / curr_visits)

    def get_state_value(self):
        # Calculate state value
        global global_t
        curr_visits = self.visits if self.visits > 0 else 0.0000000001
        return -(self.cost / curr_visits) + self.eps * (2 * math.log(global_t) / curr_visits) ** 0.5
    
    def visit(self):
        # Increment visit count
        self.visits += 1
        
    def cost_block_port(self, block_name, port_name):
        # Calculate cost for a specific block and port
        curr_cost = 0.0
        for con, freq in state.map_connectivity[block_name + '.' + port_name]:
            IP, port2 = con.split(".")
            curr_cost += self.get_dist(state.map_blocks[block_name], state.map_blocks[IP], port_name, port2)
        return curr_cost

    def calculate_dist(self):
        # Calculate total distance for all connections
        self.total_cost = 0.0
        for con1 in state.map_connectivity.keys():
            ip1, port1 = con1.split('.')
            for ip_port in state.map_connectivity[con1]:
                ip2, port2 = ip_port[0].split('.')
                self.total_cost += self.get_dist(state.map_blocks[ip1], state.map_blocks[ip2], port1, port2)
        self.total_cost /= 2.0
        return self.total_cost

    def get_dist(self, block1_index, block2_index, port1, port2, is_HPWL=False):
        # Calculate Euclidean distance or HPWL between two ports
        x1_l, y1_l, x1_r, y1_r = self.blocks[block1_index].get_port_pos(port1)
        x2_l, y2_l, x2_r, y2_r = self.blocks[block2_index].get_port_pos(port2)
        x1, y1 = (x1_l + x1_r) / 2.0, (y1_l + y1_r) / 2.0
        x2, y2 = (x2_l + x2_r) / 2.0, (y2_l + y2_r) / 2.0

        if is_HPWL:
            return abs(x2 - x1) + abs(y2 - y1)
        else:
            return ((x2 - x1) ** 2 + (y2 - y1) ** 2) ** 0.5

    def get_overlap_cost(self):
        # Calculate overlap cost for the current state
        overlap_cost = 0
        for block in self.blocks:
            overlap_cost += block.total_overlap()
        return overlap_cost

    def get_total_cost(self):
        # Calculate total cost combining connection and overlap costs
        connection_cost = self.calculate_dist()
        overlap_cost = self.get_overlap_cost()
        return connection_cost + self.penalty * overlap_cost
    
    def export_port_positions(self, file_path="tests/dataset_3_output.csv"):
        # Export port positions to a specified file
        with open(file_path, "w") as f:
            for block in self.blocks:
                for port, edge, pos in block.block_ports:
                    port_id = port.get_port_id()
                    x_l, y_l, x_r, y_r = block.get_port_pos(port_id)
                    if max(abs(y_r - y_l), abs(x_l - x_r)) > block.edges[edge][0]:
                        continue
                    f.write(f"{port_id}, {{ {x_l} {y_l} }} {{ {x_l} {y_r} }} {{ {x_r} {y_r} }} {{ {x_r} {y_l} }}\n")
