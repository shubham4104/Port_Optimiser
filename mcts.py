import random
import time
import matplotlib.pyplot as plt
import math
from state import state
from block_ip import BlockIP
from port import Port
import re

class MCTS:
    def __init__(self):
        # Initialize the MCTS with default values and empty structures.
        self.root = None
        self.block_list = []
        self.map_blocks = {}
        self.map_connectivity = {}
        self.run_blocks_once = True
        self.run_connectivity_once = True
        self.max_height = 1000
        self.action_set = []
        self.alpha = 10
        self.step_decay = 1.0003

    def set_root(self):
        # Set the root of the MCTS tree.
        self.root = state(self.block_list)
        self.root.initialise_class(self.block_list, self.map_blocks, self.map_connectivity, self.action_set)
        self.root.init_unexplored()

    def preprocess_blocks(self):
        # Process blocks to set up their edges and possible actions.
        for block in self.block_list:
            block.process_edges()
        for block in self.block_list:
            for port, edge, pos in block.block_ports:
                self.action_set.append([self.map_blocks[block.get_block_id()], port.get_port_id(), +1])
                self.action_set.append([self.map_blocks[block.get_block_id()], port.get_port_id(), -1])

    def parse_blocks(self, file_path='tests/new_tests/block.csv'):
        # Parse block information from a file.
        if self.run_blocks_once:
            self.block_list = []
            self.map_blocks = {}
            index = 0
            with open(file_path) as f:
                for lines in f:
                    IP, coords = lines.strip().split(",")
                    coord_list = []
                    for coord in re.findall('{(.+?)}', coords):
                        a, b = coord.split(" ")
                        coord_list.append([int(a), int(b)])
                    if coord_list:
                        curr_block = BlockIP(IP, coord_list, alpha=self.alpha, step_decay=self.step_decay)
                        self.block_list.append(curr_block)
                        self.map_blocks[IP] = index
                        index += 1
            self.run_blocks_once = False

    def parse_ports(self, file_path='tests/new_tests/con.csv'):
        # Parse port connections from a file.
        IP_port_pair = {}
        if self.run_connectivity_once:
            self.run_connectivity_once = False
            self.map_connectivity = {}
            index = 0
            with open(file_path) as f:
                for lines in f:
                    row = lines.strip().split(", ")
                    if len(row) == 4:
                        con1, con2, length, freq = row
                        IP1, port1 = con1.split(".")
                        IP2, port2 = con2.split(".")

                        if con1 not in IP_port_pair.keys():
                            port_obj1 = Port(port1, int(length))
                            self.block_list[self.map_blocks[IP1]].add_port(port_obj1)
                            IP_port_pair[con1] = 1

                        if con2 not in IP_port_pair.keys():
                            port_obj2 = Port(port2, int(length))
                            self.block_list[self.map_blocks[IP2]].add_port(port_obj2)
                            IP_port_pair[con2] = 1

                        if con1 in self.map_connectivity.keys():
                            self.map_connectivity[con1].append([con2, int(freq)])
                        else:
                            self.map_connectivity[con1] = [[con2, int(freq)]]

                        if con2 in self.map_connectivity.keys():
                            self.map_connectivity[con2].append([con1, int(freq)])
                        else:
                            self.map_connectivity[con2] = [[con1, int(freq)]]
    def simulated_annealing(self, curr_state, temperature=100000, iterations=100000, flag=False): 
        #Perform simulated annealing optimization on the current state.
        result = []  # Stores cost at each iteration if flag is True.

        for iter in range(iterations):
            # Choose a random action from the action set.
            block_id, port_id, direct = random.choice(self.action_set)  

            # Calculate current cost components.
            curr_block_port_cost = curr_state.cost_block_port(self.block_list[block_id].get_block_id(), port_id)
            curr_block_overlap_cost = curr_state.blocks[block_id].overlap_cost
            
            # Move port according to chosen action.
            curr_state.blocks[block_id].move_port(curr_state.blocks[block_id].get_port_index(port_id), direct)

            # Calculate cost components after the move.
            next_block_port_cost = curr_state.cost_block_port(self.block_list[block_id].get_block_id(), port_id)
            next_block_overlap_cost = curr_state.blocks[block_id].overlap_cost

            # Calculate the change in cost due to the move.
            delta = -curr_block_port_cost + next_block_port_cost + (next_block_overlap_cost - curr_block_overlap_cost) * curr_state.penalty

            # If the change in cost is positive, consider undoing the move.
            if delta > 0:
                p = math.exp(-delta * iter / temperature)
                if p < 0.5:
                    # Undo the move if acceptance probability is low.
                    curr_state.blocks[block_id].move_port(curr_state.blocks[block_id].get_port_index(port_id), -direct)

            # Record the current total cost if flag is True.
            if flag:
                result.append(curr_state.get_total_cost())

        # If flag is True, plot the cost over iterations.
        if flag:
            plt.plot(result)

        # Return the final total cost.
        return curr_state.get_total_cost()

    def expand(self, curr_state):
        #Expand the current state by adding a child state based on the next action.
        count = len(curr_state.children)
        block_id, port_id, direct = self.action_set[count]
        child = copy(curr_state)
        child.parent = curr_state
        child.children = []
        child.blocks = deepcopy(curr_state.blocks)
        child.blocks[block_id].move_port(child.blocks[block_id].get_port_index(port_id), direct)
        child.level += 1
        curr_state.children.append(child)
        return child

    def tree_policy(self, curr_state):
        #Determines the next state to visit in the MCTS.
        level = 1
        for i in range(self.max_height):
            if len(curr_state.children) != len(self.action_set):
                return [self.expand(curr_state), level]
            else:
                curr_state = curr_state.best_child()
                level += 1
        return [curr_state, level]

    def default_policy(self, curr_state):
        #Default policy for MCTS, selects random actions.
        next_state = deepcopy(curr_state)
        level = 1
        for index in range(next_state.level, next_state.level + 100):
            rand_index = random.choice(range(len(self.action_set)))
            block_id, port_id, direct = self.action_set[rand_index]
            next_state.blocks[block_id].move_port(next_state.blocks[block_id].get_port_index(port_id), direct)
            level += 1
        return [next_state.get_total_cost(), level]

    def backup(self, curr_node, cost):
        #Backpropagates the cost through the path of visited nodes.
        while curr_node.level != 0:
            curr_node.visit()
            curr_node.cost += cost
            curr_node = curr_node.parent

    def traverse_final(self, curr_state):
        #Traverses the tree to find the final state.
        while len(curr_state.children) != 0:
            curr_state = curr_state.best_child_traverse()
        return curr_state

    def perform_MCTS(self, root):
        #Perform the Monte Carlo Tree Search.
        global global_t
        outputs = []
        for i in range(1000):
            s, level = self.tree_policy(root)
            cost = self.simulated_annealing(s, iterations=level * 1000, temperature=level * 1000)
            outputs.append(cost)
            self.backup(s, cost)
            global_t += 1
        return outputs