#=============================================================================
# this is the main file importing all other files and classes and executing all of it
#=============================================================================
# hello world!
import networkx as nx
import matplotlib.pyplot as plt
import Graph
import NodeClass as nde
import SBAClass as sba
import AHBPClass as ahbp
import random
import numpy as np
from collections import OrderedDict
import itertools as it


def check_nodes(graph):
    """
    Check if all nodes in the graph already got all messages

    Note that the criterium for having all nodes is rather easy since we
    initialize all nodes with only  one message at the beginning.
    Thus at the end the data_stack has to contain 10 different messages.

    Arguments:
    graph -- networkx Graph object

    Return-type:
    True -- if all nodes contain all messages
    False -- if not everything is known to all messages
    """
    size = len(graph)
    for node in graph.nodes_iter():
        if len(node.data_stack) == size:
            pass
        elif len(node.data_stack) < size:
            return False
    return True


def get_message_counter(graph):
    """
    Compute the total number of sent messages in the network

    Iterate through all the nodes in the network and add up their
    message_counter to get the total number.

    Arguments:
    graph -- networkx Graph representing the network

    Return-type:
    total_number -- total number of sent messages
    """
    total_number = 0
    numbers = []
    for node in graph.nodes():
        # node_counter = 5*len(node.message_counter)
        # numbers.append(node_counter)
        node_counter = 0
        for number in node.message_counter:
            node_counter += number
            total_number += number
        numbers.append(node_counter)
    # substract 5 because we don't want to count the own message
    max_number = max(numbers) - 5
    # delete comment for use later
    return total_number, max_number


def setup_sending_flooding(graph):
    """
    Perfrom the sending process according to pure flooding

    Iterates through all nodes in the graph.
    The sending part and message-updating part are split.
    -> a message is not rebroadcasted mulitpletimes in the same iteration

    Arguments:
    graph -- a graph with node instances as vertices
    iteration -- number of iteration done during the sending
    FLAG -- string which indicates the broadcast algorithm

    Return-type:
    none
    """
    flag = 'flooding'
    # initate all nodes with a datapacket
    for node in graph.nodes():
        node.init_1_data()
    # loop through all nodes and their neighbours and push data from
    # its own sending_buffer to its neighbour's receive_buffer
    iteration = 0
    while not check_nodes(graph):
        for node in graph.nodes():
            # check if node rebroadcasts any messages
            node.send_to_neighbor(graph.neighbors(node))
        # before updating the sending_buffer delete already sent data
        # after update del receive_buffer not to check already known data twice
        for node in graph.nodes():
            node.del_sending_buffer()
            node.update_data(flag)
            node.del_receive_buffer()
        iteration += 1
        #Graph.print_all_data_stacks(graph)


def setup_sending_SBA(graph, timer):
    """
    Perform the sending process according to the SBA

    Iterates through all nodes in the graph.
    The sending part and message-updating part are split.
    -> a message is not rebroadcasted mulitpletimes in the same iteration
    Message-updating:
    - Check vertex-message pairs with an active random timer
    - After sending check the receive-buffer for unknown messages

    Arguments:
    graph -- a graph with node instances as vertices
    iteration -- number of iteration done during the sending
    FLAG -- string which indicates the broadcast algorithm

    Return-type:
    none
    """
    flag = 'SBA'
    # initiate all nodes with a data packet
    for node in graph.nodes():
        node.init_1_data()
        node.build_2_hop(graph)
    # update each packet_dict, containing all the packets
    # that currently have an active random timer
    iteration = 0
    while not check_nodes(graph):
        for node in graph.nodes():
            sba.check_receive_buffer(node, iteration, timer)
        for node in graph.nodes():
            sba.update_packet_dict(node, iteration)
        # forward packet in the sending list to neighbors
        for node in graph.nodes():
            # check if node rebroadcasts any messages
            node.send_to_neighbor(node.two_hop_dict.keys())
            node.del_sending_buffer()
        # # checks incoming packets if they are already known and adds
        # # them if necessary to the packet dict and activates a timer
        # for node in graph.nodes():
        #     for packet in node.receive_buffer:
        #         sba.check_receive_buffer(node, packet, iteration, graph, timer)
        # # before updating the sending_buffer delete already sent data
        # # after update del receive_buffer not to check already known data twice
        # for node in graph.nodes():
        #     node.del_sending_buffer()
        #     node.update_data(flag)
        #     node.del_receive_buffer()
        iteration += 1
    return iteration


def setup_sending_AHBP(graph):
    """
    Perfrom the sending process according to the AHBP

    Iterates through all nodes in the graph.
    The sending part and message-updating part are split.
    -> a message is not rebroadcasted mulitpletimes in the same iteration
    Message-updating:Check the receive-buffer and if needed build the BRG-set

    Arguments:
    graph -- a graph with node instances as vertices
    iteration -- number of iteration done during the sending
    timer -- parameter for the random-timer

    Return-type:
    none
    """
    # initiate the nodes with a data packet
    for node in graph.nodes_iter():
        node.init_1_data()
        # only use this until hello protocol is implemented
        # this gets the 2-hop neighbor hood form the 'master'-graph
        node.build_2_hop(graph)
        # with open("node_" + str(node.ID + 1) + '.txt', 'w') as outfile:
        #     outfile.write("new file for node :" + str(node.ID + 1) + "\n")

    iteration = 0
    while not check_nodes(graph):
        # split up the process of checking the receive_buffer
        # and sending to neighbor, such that can only traverse
        # one edge during an iteration step

        for node in graph.nodes():
            ahbp.check_receive_buffer(node, iteration)
            node.del_receive_buffer()

            # for all messages in the sending_buffer build the BRG-Set
            for message in node.sending_buffer:
                ahbp.build_BRG(node, message)

        if check_nodes(graph):
            break

        # rebroadcast the messages in the sending_buffer to the neighbors
        for node in graph.nodes_iter():
            # check if node rebroadcasts any messages
            node.send_to_neighbor(node.two_hop_dict.keys())
            node.del_sending_buffer()
        iteration += 1


def setup_sending_half_sba(graph):
    """
    Perform the sending process according to parts of the SBA

    The parts with the random are cut out.
    Besides that everything is the same as in the complete SBA

    Arguments:
    graph -- networkx.Graph instance; contains the whole network

    Return-type:
    None
    """
    for node in graph.nodes():
        node.init_1_data()
        node.build_2_hop(graph)

    iteration = 0
    while not check_nodes(graph):
        for node in graph.nodes():
            # check if node rebroadcasts any messages
            node.send_to_neighbor(node.two_hop_dict.keys())
            node.del_sending_buffer()

        for node in graph.nodes_iter():
            for message in node.receive_buffer:
                boolean = node.check_data_stack(message)
                if not boolean:
                    message.add_to_path(node)
                    node.data_stack.append(message)
                    if not sba.check_neigh(node, message.last_node):
                       node.sending_buffer.append(message)

            node.del_receive_buffer()
        iteration += 1


def setup_graph(laplacian):
    """
    Create a graph object with Node-instances according to the laplacian

    Arguments:
    laplacian -- numpy.array with the laplacian matrix of the graph
    iteration -- number of iteration for the sending-history (default = 0)

    Return-type:
    my_graph -- networkx Graph object
    """
    nde.Node.obj_counter = 0
    # this block adds the nodes to the graph and creates two dict
    # in order to label the graph correctly
    size = len(laplacian[0, :])
    my_graph = nx.Graph()
    for i in range(size):
        # depending on the mode add the arguments in the node initiator
        my_graph.add_node(nde.Node(), name=str(i + 1), color='blue')
        #my_graph.add_node(nde.Node(size, iteration), name=str(i + 1))
    # stores the nodes and their name attributes in a dictionary
    nodes_names = nx.get_node_attributes(my_graph, "name")
    # switches key and values--> thus names_nodes
    names_nodes = dict(zip(nodes_names.values(), nodes_names.keys()))

    # this block adds the edges between the nodes
    for i in range(0, size):
        for j in range(i + 1, size):
            if laplacian[i, j] == -1:
                node_1 = names_nodes[str(i + 1)]
                node_2 = names_nodes[str(j + 1)]
                my_graph.add_edge(node_1, node_2)

    return my_graph


def create_figure(graph):
    """Call other functions to create the plots"""
    Graph.iteration_plots(graph)

    # # creates all the animated plots for the nodes
    # size = len(graph.nodes())
    # for i in range(size):
    #     fig = plt.figure()
    #     Graph.bar_plot(graph, i + 1, fig)

    print 'check plot generating'


def get_num_sender(graph):
    """Iterate through graph and count true sender flags"""
    rebroadcaster = 0
    for node in graph.nodes_iter():
        if node.sender:
            rebroadcaster += 1
    return rebroadcaster


def average_degree(graph):
    """Compute the average degree of all the vertices in the graph"""
    av_deg = 0
    for node in graph.nodes_iter():
        av_deg += graph.degree(node)
    av_deg /= float(len(graph))
    return av_deg


def clear_graph_data(graph):
    """Clear counter, flags and messages in the graph"""
    for node in graph.nodes_iter():
        node.del_sending_buffer()
        node.del_receive_buffer()
        node.del_data_stack()
        node.sender = False
        node.message_counter = []


def random_graph(num_nodes):
    laplacian_array = build_rand_graph(num_nodes)
    rand_graph = setup_graph(laplacian_array)
    return rand_graph, laplacian_array


def build_line_laplacian(size):
    """
    Build laplacian of line-graph and return it as numpy.array"""
    my_ar = np.eye(size)
    if size == 2:
        my_ar = np.array([[1, -1],
                          [-1, 1]])
    for i in range(1, size-1):
        my_ar[i, i] += 1
        my_ar[i-1, i] = -1
        my_ar[i+1, i] = -1
        my_ar[i, i-1] = -1
        my_ar[i, i+1] = -1
    return my_ar


def get_connectivity(laplacian):
    """
    Compute the algebraic connectivity of a graph

    Arguments:
    laplacian -- Laplace matrix of a graph

    Return-type:
    connectivity -- float; algebraic connectivity
    """
    val, vec = np.linalg.eig(laplacian)
    val.sort()
    return val[1]


def test_connectivity():
    conn_dict = {}
    conn_lst = []
    for i in range(1000):
        graph, laplacian = random_graph(4)
        con = get_connectivity(laplacian)
        conn_lst.append(nx.average_node_connectivity(graph))
        conn_lst.sort()
        print con
        # if con < 0.74 and con>0.73:
        #     Graph.print_graph(graph)
        if 1.43 < con < 2.45:
            Graph.print_graph(graph)
        con = abs(con)
        con = round(con, 3)
        if con not in conn_dict:
            conn_dict[con] = 0
        conn_dict[con] += 1
    con_lst = OrderedDict(sorted(conn_dict.items()))
    # print conn_lst
    # print con_lst


def do_plots(flood_lst, ahbp_lst, sba_lst, half_sba, ax, mode):
    """
    Plot results of each algorithm

    Dictionaries contain connectivity as key and mean value and standart deviation as values
    Plot, with errorbars, all in the same axes-object.

    Arguments:
    flood_lst -- list with the values for flooding
    ahbp_lst -- list with the values for the ahbp
    sba_lst -- list with the values for the sba
    half_sba_lst -- list with the values for a simplified version of the sba
    ax -- axes object into which the data will be plotted
    mode -- integer for choosing the y-axis label

    Return-type:
    None
    """
    conn_flood, y_flood, flood_err = sort_dict(flood_lst)
    conn_ahbp, y_ahbp, ahbp_err = sort_dict(ahbp_lst)
    conn_sba, y_sba, sba_err = sort_dict(sba_lst)
    conn_half_sba, y_half_sba, half_sba_err = sort_dict(half_sba)

    ax.errorbar(conn_flood, y_flood, yerr=flood_err, marker='o')
    ax.errorbar(conn_ahbp, y_ahbp, yerr=ahbp_err, color='red', marker='s')
    ax.errorbar(conn_half_sba, y_half_sba, yerr=half_sba_err, color='green', marker='^')
    ax.errorbar(conn_sba, y_sba, yerr=sba_err, color='orange', marker='D', capthick=3)

    ax.xaxis.set_label_text('Graph size')
    if mode == 1:
        ax.yaxis.set_label_text('Retransmitter')
    elif mode == 2:
        ax.yaxis.set_label_text('Messages sent')
    elif mode == 3:
        ax.yaxis.set_label_text('Max Bufferlength')


def sort_dict(raw_dict):
    """
    Sort the tuples in the list and unzip it into connectivity and y-value

    Argument:
    raw_dict -- dict with key: connectivity; values: [y-average, y-std]

    Return-types:
    conn_lst -- lst containing the connectivity values
    y_lst -- lst containing the average
    y_error -- lst containint the standart deviation
    """
    ordered_lst = OrderedDict(sorted(raw_dict.items()))
    conn_lst = ordered_lst.keys()
    y_lst = [a[0] for a in ordered_lst.values()]
    y_error = [a[1] for a in ordered_lst.values()]
    return conn_lst, y_lst, y_error


def average_std(value_dict):
    """
    Compute the average and std for the values of the input dictionary

    Argument:
    value_dict -- dictionary with key: connectivity; values: [ measured values ]

    Return-type:
    value_dict -- dictionary now with key: connectivity; values: [ average, std ]
    """
    for number in value_dict:
        average = np.average(value_dict[number])
        deviation = np.std(value_dict[number])
        value_dict[number] = [average, deviation]
    return value_dict


def update_dict(mes_dict, rebroad_dict, max_dict, conn, rebroad, mes, max_mes):
    """
    Check if conn is already key and append rebroad, mes

    Argument:
    mes_dict -- dictionary containing the total number of messages
    rebroad_dict -- dictionary conatining the number of rebroadcaster
    conn -- connectivity of the graph
    rebroad -- number of rebroadcaster measured for the sample
    mes -- total messages measured for the sample

    Return-type:
    rebroad_dict -- updated rebroad_dict
    mes_dict -- updated message_dict
    """
    if conn not in mes_dict:
        mes_dict[conn] = []
    if conn not in rebroad_dict:
        rebroad_dict[conn] = []
    if conn not in max_dict:
        max_dict[conn] = []

    max_dict[conn].append(max_mes)
    mes_dict[conn].append(mes)
    rebroad_dict[conn].append(rebroad)
    return rebroad_dict, mes_dict, max_dict

def test_sba():
    """
    Test function to investigate certain graphs

    Choose the graph size and the number of samples.
    Then let a certain broadcasting algorithm run over the graph.
    Print graph topologies with desired connectivities and later on
    print all the collected data from the samples
    """
    size = 6
    samples = 2000

    fig = plt.figure('sba')
    ax1 = fig.add_subplot(2, 1, 1)
    ax2 = fig.add_subplot(2, 1, 2)
    x_lst = []
    messages = []
    rebroadcaster = []
    for i in range(samples):
        graph, laplacian = random_graph(size)
        # graph dont makes any sense right now, cuz x-lst is not right
        x_lst.append(get_connectivity(laplacian))
        if 1.4 > x_lst[-1] > 1.3:
            setup_sending_SBA(graph, 5)
            mes_num, max_mes = get_message_counter(graph)
            messages.append(mes_num)
            rebroadcaster.append(get_num_sender(graph))
        # if 1.1 > x_lst[-1] > 0.9:
            print x_lst[-1], messages[-1], rebroadcaster[-1]
            # Graph.print_graph(graph)
    print x_lst
    print messages
    print rebroadcaster
    mx = zip(x_lst, messages)
    mx.sort()
    xm, messages = zip(*mx)

    rx = zip(x_lst, rebroadcaster)
    rx.sort()
    xr, rebroadcaster = zip(*rx)
    print xm, messages
    print xr, rebroadcaster

    ax1.plot(xm, messages, marker='o')
    ax2.plot(xr, rebroadcaster, marker='o')
    plt.show()


def arrange_data(flood, ahbp_dict, sba_dict, half_sba_dict):
    """
    Delete all entries in ahbp, sba, half_sba which are equal to the corresponding in the flood list

    Dictionaries with algebraic connectivity as key and max number of messages processed as value
    If the latter 3 dictionaries have a value for a key equal to the one in the flood-dict then delete it.
    Lastly turn them into OrderedDict( dictionaries that can be sorted)

    Arguments:
    flood -- Dictionary containing the data from flooding the graph
    ahbp_dict -- Dictionary containing the data from performing the AHBP algorithm
    sba_dict -- Dictionary containing the data from performing the SBA algorithm
    half_sba_dict -- Dictionary containing the data from performing only parts of the SBA algorithm

    Return-type:
    ordered_flood -- OrderedDict; contains the same as flood
    ordered_ahbp -- OrderedDict; filtered ahbp_dict
    ordered_sba -- OrderedDict; filtered sba_dict
    ordered_half_sba -- OrderedDict; fileredt half_sba_dict
    """
    for conn in ahbp_dict:
        deleter = []
        for number in ahbp_dict[conn]:
            if number == 0:
                deleter.append(0)
        for zero in deleter:
            ahbp_dict[conn].remove(zero)
    for conn in sba_dict:
        deleter = []
        for number in sba_dict[conn]:
            if number == 0:
                deleter.append(0)
        for zero in deleter:
            sba_dict[conn].remove(zero)
    for conn in half_sba_dict:
        deleter = []
        for number in half_sba_dict[conn]:
            if number == 0:
                deleter.append(0)
        for zero in deleter:
            half_sba_dict[conn].remove(zero)
    for conn, values in ahbp_dict.items():
        if values == []:
            del ahbp_dict[conn]
    for conn, values in sba_dict.items():
        if values == []:
            del sba_dict[conn]
    for conn, values in half_sba_dict.items():
        if values == []:
            del half_sba_dict[conn]
    ordered_flood = OrderedDict(flood)
    ordered_ahbp = OrderedDict(ahbp_dict)
    ordered_sba = OrderedDict(sba_dict)
    ordered_half_sba = OrderedDict(half_sba_dict)
    print ordered_flood
    print ordered_ahbp
    print ordered_sba
    print ordered_half_sba

    return ordered_flood, ordered_ahbp, ordered_sba, ordered_half_sba


def buffer_plots():
    """
    Calculate the number of messages/tasks one DFA would have to do

    First build choose the max graphsize up to which you want to calculate it,
    then the number of samples for each size.
    Generate random graphs and perform each broadcasting algorithm on it.
    Then get the maximum of processed messages out of the graph.
    Finally plot it according to the graph's connectivity.

    Argument:
    --
    Return-type:
    Plot a graph with possibility to arrange and save it manually
    """
    max_size = 14
    samples = 200

    x_lst = [i for i in range(2, max_size+1)]


    fig = plt.figure('Max buffer-length')

    for size in x_lst:
        print size

        ax = fig.add_subplot(max_size/2, 2, size-1)

        flood_mes = {}
        ahbp_mes = {}
        sba_mes = {}
        half_sba_mes = {}

        flood_rebroad = {}
        ahbp_rebroad = {}
        sba_rebroad = {}
        half_rebroad = {}

        flood_max = {}
        ahbp_max = {}
        sba_max = {}
        half_sba_max = {}

        # for a in range(samples):
        for a in range(samples):
            conn = -1
            while conn < 0:
                graph, laplacian = random_graph(size)
                conn = round(get_connectivity(laplacian), 2)
            # get values for flooding
            setup_sending_flooding(graph)
            messages, max_mes_flood = get_message_counter(graph)
            rebroadcaster = get_num_sender(graph)
            flood_rebroad, flood_mes, flood_max = update_dict(flood_mes, flood_rebroad, flood_max, conn, rebroadcaster, messages, max_mes_flood)
            # set all the sender flags to false again
            # so one can reuse the same graph
            clear_graph_data(graph)
            # get values for AHBP
            setup_sending_AHBP(graph)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            if max_mes == max_mes_flood:
                max_mes = 0
            ahbp_rebroad, ahbp_mes, ahbp_max = update_dict(ahbp_mes, ahbp_rebroad, ahbp_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)
            # get values for SBA
            setup_sending_half_sba(graph)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            if max_mes == max_mes_flood:
                max_mes = 0
            half_rebroad, half_sba_mes, half_sba_max = update_dict(half_sba_mes, half_rebroad, half_sba_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)
            iteration = setup_sending_SBA(graph, 2)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            if max_mes == max_mes_flood:
                max_mes = 0
            sba_rebroad, sba_mes, sba_max = update_dict(sba_mes, sba_rebroad, sba_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)

        flood_max, ahbp_max, sba_max, half_sba_max = arrange_data(flood_max, ahbp_max, sba_max, half_sba_max)
        flood_conn = flood_max.keys()
        flood_y = flood_max.values()
        flood_x = []
        for i in range(len(flood_conn)):
            for j in range(len(flood_y[i])):
                flood_x.append(flood_conn[i])
        flood_y = list(it.chain.from_iterable(flood_y))
        ax.plot(flood_x, flood_y, linestyle='None', marker='o', color='blue')
        ahbp_conn = ahbp_max.keys()
        ahbp_y = ahbp_max.values()
        ahbp_x = []
        for i in range(len(ahbp_conn)):
            for j in range(len(ahbp_y[i])):
                ahbp_x.append(ahbp_conn[i])
        ahbp_y = list(it.chain.from_iterable(ahbp_y))
        ax.plot(ahbp_x, ahbp_y, linestyle='None', marker='s', color='red')
        sba_conn =sba_max.keys()
        sba_y = sba_max.values()
        sba_x = []
        for i in range(len(sba_conn)):
            for j in range(len(sba_y[i])):
                sba_x.append(sba_conn[i])
        sba_y = list(it.chain.from_iterable(sba_y))
        ax.plot(sba_x, sba_y, linestyle='None', marker='D', color='orange')
        half_sba_conn = half_sba_max.keys()
        half_sba_y = half_sba_max.values()
        half_sba_x = []
        for i in range(len(half_sba_conn)):
            for j in range(len(half_sba_y[i])):
                half_sba_x.append(half_sba_conn[i])
        half_sba_y = list(it.chain.from_iterable(half_sba_y))
        ax.plot(half_sba_x, half_sba_y,linestyle='None', marker='^', color='green')

    # sometimes one needs to hack a lil bit
    # access the matplotlib.line objects through it
    lines = fig._axstack._elements[0][1][1].lines
    print lines

    fig.legend((lines[0], lines[1], lines[2], lines[3]),
                ('flood', 'ahbp', 'sba', 'half_sba'), 'lower right')
    plt.show()


def test_plots():  # currently everything except the flooding is disabled in this function
    max_size = 8
    samples = 100

    x_lst = [i for i in range(2, max_size+1)]

    x_lst = [15, 20, 30, 40, 50, 75, 100]

    fig1 = plt.figure('Total messages')
    fig2 = plt.figure('Number of rebroadcaster')
    # fig3 = plt.figure('Max buffer-length')

    for size in range(len(x_lst)):
        print x_lst[size]
        ax1 = fig1.add_subplot(max_size/2, 2, size+1)
        ax2 = fig2.add_subplot(max_size/2, 2, size+1)
        # ax3 = fig3.add_subplot(max_size/2, 2, size-1)

        flood_mes = {}
        ahbp_mes = {}
        sba_mes = {}
        half_sba_mes = {}

        flood_rebroad = {}
        ahbp_rebroad = {}
        sba_rebroad = {}
        half_rebroad = {}

        flood_max = {}
        ahbp_max = {}
        sba_max = {}
        half_sba_max = {}

        # for a in range(samples):
        for a in range(samples):
            conn = -1
            while conn < 0:
                graph, laplacian = random_graph(x_lst[size])
                conn = round(get_connectivity(laplacian), 2)
            # get values for flooding
            print 'flooding'
            setup_sending_flooding(graph)
            messages, max_mes = get_message_counter(graph)
            rebroadcaster = get_num_sender(graph)
            flood_rebroad, flood_mes, flood_max = update_dict(flood_mes, flood_rebroad, flood_max, conn, rebroadcaster, messages, max_mes)
            # set all the sender flags to false again
            # so one can reuse the same graph
            clear_graph_data(graph)
            # get values for AHBP
            print 'ahbp'
            setup_sending_AHBP(graph)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            ahbp_rebroad, ahbp_mes, ahbp_max = update_dict(ahbp_mes, ahbp_rebroad, ahbp_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)
            # get values for SBA
            print 'half_sba'
            setup_sending_half_sba(graph)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            half_rebroad, half_sba_mes, half_sba_max = update_dict(half_sba_mes, half_rebroad, half_sba_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)
            print 'sba'
            iteration = setup_sending_SBA(graph, 2)
            rebroadcaster = get_num_sender(graph)
            messages, max_mes = get_message_counter(graph)
            sba_rebroad, sba_mes, sba_max = update_dict(sba_mes, sba_rebroad, sba_max, conn, rebroadcaster, messages, max_mes)
            clear_graph_data(graph)

        # print flood_mes

        flood_mes = average_std(flood_mes)
        ahbp_mes = average_std(ahbp_mes)
        half_sba_mes = average_std(half_sba_mes)
        sba_mes = average_std(sba_mes)

        flood_rebroad = average_std(flood_rebroad)
        ahbp_rebroad = average_std(ahbp_rebroad)
        sba_rebroad = average_std(sba_rebroad)
        half_rebroad = average_std(half_rebroad)


        # flood_max = average_std(flood_max)
        # ahbp_max = average_std(ahbp_max)
        # half_sba_max = average_std(half_sba_max)
        # sba_max = average_std(sba_max)

        # do_plots(flood_max, ahbp_max, sba_max, half_sba_max, ax3, 3)

        do_plots(flood_mes, ahbp_mes, sba_mes, half_sba_mes, ax1, 2)

        do_plots(flood_rebroad, ahbp_rebroad, sba_rebroad, half_rebroad, ax2, 1)

    # sometimes one needs to hack a lil bit
    # access the matplotlib.line objects through
    lines1 = fig1._axstack._elements[0][1][1].lines
    lines2 = fig2._axstack._elements[0][1][1].lines
    # lines3 = fig3._axstack._elements[0][1][1].lines

    fig1.legend((lines1[2], lines1[5], lines1[8], lines1[11]),
                ('flood', 'ahbp', 'half_sba', 'sba'), 'lower right')
    fig2.legend((lines2[2], lines2[5], lines2[8], lines2[11]),
                ('flood', 'ahbp', 'half_sba', 'sba'), 'lower right')
    # fig3.legend((lines3[2], lines3[5], lines3[8], lines3[11]),
    #             ('flood', 'ahbp', 'half_sba', 'sba'), 'lower right')
    plt.show()


def lattice_graph(length):
    """
    Build a hexagonally gridded graph of a square shaped form

    The grid has a squared shape of size = length.
    First create a square grid graph then add edges on the diagonals.

    Arguments:
    length -- integer determining the size of the square

    Return-type:
    graph -- networkx.Graph object
    """
    # builds a square grid graph
    graph = nx.grid_2d_graph(length, length)
    # in each square add an edge on the diagonal -> hexagonal shape
    # add edges to seperate list, cuz cannot modifiy the graph during iteration
    edge_lst = []
    for n in graph:
        x, y = n
        if y > 0 and x < length-1:
            edge_lst.append((n, (x+1, y-1)))
    graph.add_edges_from(edge_lst)
    return graph


def build_rand_graph(num_nodes):
    """
    Build the DFA-like random graph

    First build a hexagonally gridded graph -> call 'lattice_graph()'
    Then delete random nodes till num_nodes nodes remain.
    If deleting a node results in cutting the graph into mutliple components
    check if one of the subgraphs has still enough vertices.
    Continue computation with this subgraph.
    Else delete another vertex.
    Return the laplacian representation of the graph

    Arguments:
    num_nodes -- number of nodes the resulting graph should have

    Return-type:
    laplacian-matrix -- numpy array
    """
    # root = math.sqrt(num_nodes)
    # length = int(math.ceil(root))
    graph = lattice_graph(num_nodes)
    # for node_name in graph.node:
    #     graph.node[node_name]['color'] = 'red'
    # pos = nx.spring_layout(graph)
    while len(graph) > num_nodes:
        # as long as the graph is not connect
        # after removing a node try another one
        connect_bool = False
        while not connect_bool:
            node_index = random.randint(0, len(graph)-1)
            removed_node = graph.nodes()[node_index]
            removed_edges = graph.edges(removed_node)
            # graph.node[removed_node]['color'] = 'blue'
            # colors = []
            # for node_name in graph.node:
            #     colors.append(graph.node[node_name]['color'])
            # nx.draw(graph,pos, node_color=colors)
            # plt.show()
            graph.remove_node(removed_node)
            # check if graph is still connected
            connect_bool = nx.is_connected(graph)
            if not connect_bool:
                sub_graphs_worked = False
                sub_graphs = nx.connected_component_subgraphs(graph)
                for sub in sub_graphs:
                    if len(sub) >= num_nodes:
                        sub_graphs_worked = True
                        break
                if sub_graphs_worked:
                    # for node_name in sub:
                    #     graph.node[node_name]['color'] = 'blue'
                    # colors = []
                    # for node_name in graph.node:
                    #     colors.append(graph.node[node_name]['color'])
                    # nx.draw(graph,pos, node_color=colors)
                    # plt.show()
                    # take on purpose the last sub element from the for-loop
                    graph = sub
                    connect_bool = True
                    # for node_name in graph.node:
                    #     graph.node[node_name]['color'] = 'red'

            # if graph is not connected anymore put removed node back
                else:
                    graph.add_node(removed_node)  # , color = 'red')
                    graph.add_edges_from(removed_edges)

    # nx.draw(graph)
    # plt.show()

    laplacian_matrix = nx.laplacian_matrix(graph)
    return laplacian_matrix.getA()

FLAG = ""


def main():
    """main function which performs the whole retransmission"""
    # test_connectivity()
    # test_sba()
    buffer_plots()
    # test_plots()
    # # laplacian matrix -> has the information about the network-topology
    # graph_matrix = np.array([[ 3, -1,  0, -1, -1,  0,  0,  0,  0,  0,  0,  0,  0],
    #                          [-1,  3, -1, -1,  0,  0,  0,  0,  0,  0,  0,  0,  0],
    #                          [ 0, -1,  4, -1,  0,  0, -1, -1,  0,  0,  0,  0,  0],
    #                          [-1, -1, -1,  6, -1, -1, -1,  0,  0,  0,  0,  0,  0],
    #                          [-1,  0,  0, -1,  3, -1,  0,  0,  0,  0,  0, -1,  0],
    #                          [ 0,  0,  0, -1, -1,  5, -1,  0,  0, -1, -1, -1,  0],
    #                          [ 0,  0, -1, -1,  0, -1,  6, -1, -1, -1,  0,  0,  0],
    #                          [ 0,  0, -1,  0,  0,  0, -1,  3, -1,  0,  0,  0,  0],
    #                          [ 0,  0,  0,  0,  0,  0, -1, -1,  3, -1,  0,  0,  0],
    #                          [ 0,  0,  0,  0,  0, -1, -1,  0, -1,  5, -1,  0, -1],
    #                          [ 0,  0,  0,  0,  0, -1,  0,  0,  0, -1,  4, -1, -1],
    #                          [ 0,  0,  0,  0, -1, -1,  0,  0,  0,  0, -1,  3,  0],
    #                          [ 0,  0,  0,  0,  0,  0,  0,  0,  0, -1, -1,  0,  2]])
    # val, vec = np.linalg.eig(graph_matrix)
    # val.sort()
    # print val[1]

    #==========================================================================
    # graph_matrix = np.array([[ 2, -1,  0,  0, -1,  0],
    #                          [-1,  3, -1,  0, -1,  0],
    #                          [ 0, -1,  2, -1,  0,  0],
    #                          [ 0,  0, -1,  3, -1, -1],
    #                          [-1, -1,  0, -1,  3,  0],
    #                          [ 0,  0,  0, -1,  0,  1]])
    #==========================================================================
    # graph_matrix = np.array([[ 6, -1, -1, -1, -1, -1, -1],
    #                          [-1,  3, -1,  0,  0,  0, -1],
    #                          [-1, -1,  3, -1,  0,  0,  0],
    #                          [-1,  0, -1,  3, -1,  0,  0],
    #                          [-1,  0,  0, -1,  3, -1,  0],
    #                          [-1,  0,  0,  0, -1,  3, -1],
    #                          [-1, -1,  0,  0,  0, -1, 3]])

    # graph_matrix = np.array([[4, -1, -1, -1, -1, 0],
    #                          []])
    # my_graph = setup_graph(graph_matrix, ITERATION)
    # print nx.average_node_connectivity(my_graph)
    # print nx.laplacian_matrix(my_graph)
    # print nx.clustering(my_graph)
    # build_rand_graph(5)
    # Graph.print_graph(my_graph)
    # while True:
    #     clear_graph_data(my_graph)
    #     print "Your options are as follows:\n\n"\
    #       "flooding ->\tPure Flooding in the Network\n"\
    #       "SBA ->\t\tScalable Broadcast Algorithm\n"\
    #       "AHBP ->\t\tAd-Hoc Broadcast Protocol\n"
    #     FLAG = raw_input("Enter your Flag. To quit press enter\n")
    #     if FLAG == "":
    #         print 'Application is now shutting down'
    #         break
    #     elif FLAG == "SBA":
    #         setup_sending_SBA(my_graph, ITERATION, FLAG)
    #         print get_num_sender(my_graph)
    #         set_sender_false(my_graph)
    #         print 'check SBA calculations'
    #     elif FLAG == "AHBP":
    #         setup_sending_AHBP(my_graph, ITERATION)
    #         print get_num_sender(my_graph)
    #         set_sender_false(my_graph)
    #         print 'check AHBP calculations'
    #     elif FLAG == "flooding":
    #         setup_sending_flooding(my_graph, ITERATION, FLAG)
    #         print get_num_sender(my_graph)
    #         set_sender_false(my_graph)
    #         print 'check flooding calculations'
    #     create_figure(my_graph)


if __name__ == '__main__':
    main()
