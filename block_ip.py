from copy import deepcopy
from port import Port

class BlockIP:
    def __init__(self, block_id, edge_coords, alpha=1, step_decay=1):
        # Initialize the BlockIP instance.
        self.block_id = block_id
        self.block_coords = edge_coords
        self.edges = []
        self.block_ports = []
        self.alpha = alpha
        self.step_decay = step_decay
        self.overlap_cost = 0
        self.map_port = {}

    def __deepcopy__(self, memo):
        # Create a deep copy of the BlockIP instance.
        cls = self.__class__
        obj = cls.__new__(cls)
        memo[id(self)] = obj
        for k, v in self.__dict__.items():
            setattr(obj, k, deepcopy(v, memo))
        return obj

    def get_block_coords(self):
        # Return the coordinates of the block.
        return self.block_coords

    def get_block_id(self):
        # Return the ID of the block.
        return self.block_id

    def sort_ports(self):
        # Sort the ports based on their edge number.
        self.block_ports.sort(key=lambda x: x[1])

    def process_edges(self):
        # Process the edges of the block to determine lengths and directions.
        for index in range(len(self.block_coords) - 1):
            x1, y1 = self.block_coords[index]
            x2, y2 = self.block_coords[index + 1]
            dir = 1 if (x1 != x2 and y1 < y2) or (y1 == y2 and x1 < x2) else -1
            length = abs(x1 - x2) + abs(y1 - y2)
            self.edges.append([length, dir])

    def add_port(self, port):
        # Add a port to the block.
        self.map_port[port.get_port_id()] = len(self.block_ports)
        self.block_ports.append([port, 0, 0])  # Adding port at the 0-th edge initially
        port.set_port_block(self.block_id)

    def line_overlaps(self, port1_info, port2_info):
        # Calculate if two ports on the same edge overlap.
        port1 , edge1, pos1 = port1_info
        port2 , edge2, pos2 = port2_info

        if edge1!=edge2:
            return 0

        if pos2 < pos1:
            # swap
            temp = port1 , edge1, pos1
            port1 , edge1, pos1 = [port2 , edge2, pos2]
            port2 , edge2, pos2 = temp

        len1 = port1.get_port_length()
        len2 = port2.get_port_length()
        overlap = 0
        
        if pos1 + len1 <= pos2:
            overlap = 0
        elif pos1 + len1 >=pos2 and pos2 + len2 >= pos1 + len1:
            overlap = pos1 + len1 - pos2
        elif pos1 + len1 >=pos2 and pos2 + len2 <= pos1 + len1:
            overlap = len2
        return overlap

    def edge_overlap(self, edge_id):
        # Calculate overlap on a specific edge.
        curr_len = len(self.block_ports)
        edge_ports = []
        overlap = 0
        for port_info in self.block_ports:
            port , edge, pos = port_info
            if edge == edge_id:
                edge_ports.append(port_info)
        
        for index1 in range(len(edge_ports)):
            for index2 in range(len(edge_ports)):
                if index1==index2:
                    continue
                overlap += self.line_overlaps(edge_ports[index1], edge_ports[index2])
        return overlap/2

    def total_overlap(self):
        # Calculate total overlap across all edges.
        self.overlap_cost = sum(self.edge_overlap(index) for index in range(len(self.edges)))
        return self.overlap_cost

    def move_port(self, port_id, direct):
        # Move a port to a different position on the edge.
        global global_t
        port, edge, pos = self.block_ports[port_id]
        port_len = port.get_port_length()
        pos += direct*(max(1,int(self.alpha - self.step_decay**global_t)))
        
        edge_len, edge_dir = self.edges[edge]
        new_edge = edge
        new_pos = pos

        moved_to_other_edge=False
        if pos<0:
            # move to previous edge
            moved_to_other_edge=True
            new_edge = edge-1
            if new_edge<0:
                new_edge = len(self.edges)-1
            new_pos = self.edges[new_edge][0] - port_len
        elif pos+port_len>edge_len:
            # move to next edge
            moved_to_other_edge=True
            new_edge=edge+1
            if new_edge>=len(self.edges):
                new_edge = 0
            new_pos = 0
        
        cost = -self.edge_overlap(edge) 
        if moved_to_other_edge==True:
            cost -= self.edge_overlap(new_edge)
        
        self.block_ports[port_id] = [port, new_edge, new_pos]
        
        cost += self.edge_overlap(edge)
        if moved_to_other_edge==True:
            cost += self.edge_overlap(new_edge)
        
        self.overlap_cost += cost

    def get_port_index(self, port_name):
        # Get the index of a port in the block.
        return self.map_port[port_name]

    def get_port_pos(self, port_name):
        # Get the position of a port in the block.
        port_index = self.map_port[port_name]
        port, edge, pos = self.block_ports[port_index]
        
        corner_x, corner_y  = self.block_coords[edge]
        _, direct = self.edges[edge]
        
        posx_l = corner_x
        posy_l = corner_y
        posx_r = corner_x
        posy_r = corner_y
        port_len = port.get_port_length()
        if direct == 1 and edge%2==0:
            posy_l += pos
            posx_r += Port.port_width
            posy_r += pos + port_len
        elif direct == 1 and edge%2==1:
            posx_l += pos
            posx_r += pos + port_len
            posy_r -= Port.port_width
        elif direct == -1 and edge%2==0:
            posy_l -= pos
            posx_r -= Port.port_width
            posy_r -= pos + port_len
        else:
            posx_l -= pos
            posx_r -= pos + port_len
            posy_r += Port.port_width
            
        return [posx_l, posy_l, posx_r, posy_r]

