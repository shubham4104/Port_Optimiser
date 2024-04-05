from mcts import MCTS
import time
import matplotlib.pyplot as plt
from copy import deepcopy

def main(blocks_file, ports_file, output_file):
    #Main function to initialize and run the MCTS algorithm.
    obj = MCTS()
    obj.parse_blocks(blocks_file)
    obj.parse_ports(ports_file)
    obj.preprocess_blocks()
    obj.set_root()

    t1 = time.time()
    outputs = obj.perform_MCTS(obj.root)
    t2 = time.time()
    delta = t2 - t1

    final = obj.traverse_final(obj.root)
    final.export_port_positions(output_file)
    print("final cost", final.get_total_cost())
    print(f"Time difference is {delta} seconds")
    plt.plot(outputs)

if __name__ == "__main__":
    # Define the file paths for blocks and ports
    blocks_file = 'tests/new_tests/block_4X.csv'
    ports_file = 'tests/new_tests/con_4X.csv'
    output_file = 'tests/new_tests/output_4X.csv'
    main(blocks_file, ports_file, output_file)
