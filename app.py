from flask import Flask, render_template_string, render_template, request ,jsonify
import numpy as np
import threading
import time
import random
import plotly.graph_objects as go

app = Flask(__name__)

# Predefined platform points
base_points = {
    0: (382.5, 261.251),
    1: (417.50, 200.629),
    2: (35, -461.88),
    3: (-35, -461.88),
    4: (-417.5, 200.629),
    5: (-382.50, 261.251)
}

top_points = {
    0: (27.5, 378.134),
    1: (341.25, -165.267),
    2: (313.75, -212.890),
    3: (-313.75, -212.890),
    4: (-341.25, -165.267),
    5: (-27.5, 378.164)
}

elements = [0,0,0,0,0,0,0,0,0,0,0,0]

coordinates = [100,0,0,0,0,0];    # [x , y , z , roll , pitch , yaw]
                

distance = 10;

logs = "ABC"     #Error logs 

# Extract coordinates
base_x = [p[0] for p in base_points.values()]
base_y = [p[1] for p in base_points.values()]
base_z = [0] * len(base_x)  # Base height is 0

top_x = [p[0] for p in top_points.values()]
top_y = [p[1] for p in top_points.values()]
top_z = [950] * len(top_x)  


latest_input = {"value": ""}

# Function to continuously take input from the terminal


# Function to create a 3D Stewart Platform plot
def create_stewart_platform(offset_x=0, offset_y=0, offset_z=0, roll=0 , pitch = 0, rotation=0 ,act_value=[0,0,0,0,0,0] , dgc=False):
    
    
    # Apply offsets and rotation to the top platform
    if(rotation >= 0):
        rotation_matrix = np.array([
            [np.cos(rotation), -np.sin(rotation), 0],
            [np.sin(rotation), np.cos(rotation), 0],
            [0, 0, 1],
        ])
    else:
        rotation = abs(rotation)
        rotation_matrix = np.array([
            [np.cos(-rotation), -np.sin(-rotation), 0],
            [np.sin(-rotation), np.cos(-rotation), 0],
            [0, 0, 1],
        ])

    top_points_rotated = np.dot(
        rotation_matrix,
        np.vstack((top_x, top_y, np.array(top_z) + offset_z))
    )
    top_points_rotated[0] += offset_x
    top_points_rotated[1] += offset_y

    
    top_points_rotated[2][0] += act_value[0]
    top_points_rotated[2][1] += act_value[1]
    top_points_rotated[2][2] += act_value[2]
    top_points_rotated[2][3] += act_value[3]
    top_points_rotated[2][4] += act_value[4]
    top_points_rotated[2][5] += act_value[5]

    
    # Update roll
    if(roll < 0):
        roll = abs(roll)
        top_points_rotated[2][3] += roll
        top_points_rotated[2][4] += roll
    else:
        top_points_rotated[2][1] += roll
        top_points_rotated[2][2] += roll

    # Update pitch
    if(pitch >= 0):
        top_points_rotated[2][0] += pitch
        top_points_rotated[2][5] += pitch
    else:
        pitch = abs(pitch)
        top_points_rotated[2][1] += pitch
        top_points_rotated[2][2] += pitch
        top_points_rotated[2][3] += pitch
        top_points_rotated[2][4] += pitch

    # Calculate the new center point of the top platform
    center_x = np.mean(top_points_rotated[0])
    center_y = np.mean(top_points_rotated[1])
    center_z = np.mean(top_points_rotated[2])

    # print("lenght of actuators:" , top_points_rotated[2])
    # arr = [];
    # for i in range(6):
    #     # print(top_points_rotated[2][i]-450);
    #     arr.append(float(top_points_rotated[2][i]-450));
    # print("arr:" , arr)

    # Simplified calculation of actuator lengths
    final_lengths = []
    for i in range(6):
        dx = base_x[i] - top_points_rotated[0][i]  # Difference in X-coordinates
        dy = base_y[i] - top_points_rotated[1][i]  # Difference in Y-coordinates
        dz = base_z[i] - top_points_rotated[2][i]  # Difference in Z-coordinates
        
        length = np.sqrt(dx**2 + dy**2 + dz**2)    # Calculate Euclidean distance
        print("Length of actuator", i + 1, ":", length)
        if(abs(length) < 1019):
            
            length = abs(length - 950)
        else:
            length = length - 1020.90
        final_lengths.append(round(float(abs(length)) , 1))               # Add length to the list
    
    print("Final Actuator Lengths:", final_lengths)

    # Create the figure
    fig = go.Figure()

    # Add the base platform
    fig.add_trace(go.Mesh3d(
        x=base_x,
        y=base_y,
        z=base_z,
        color='black',
        opacity=0.5,
        flatshading=True,
        name='Base Platform'
    ))

    # Add the top platform
    fig.add_trace(go.Mesh3d(
        x=top_points_rotated[0],
        y=top_points_rotated[1],
        z=top_points_rotated[2],
        color='blue',
        opacity=0.5,
        flatshading=True,
        name='Top Platform'
    ))

    # Add the center point (updated based on top platform position)
    
    if(dgc == "True"):
        fig.add_trace(go.Scatter3d(
            x=[center_x],
            y=[center_y],
            z=[center_z],
            mode='markers',
            marker=dict(size=4, color='green', symbol='circle'),
            name='Center Point'
        ))
       
    else:
        fig.add_trace(go.Scatter3d(
            x=[center_x],
            y=[center_y],
            z=[center_z],
            mode='markers',
            marker=dict(size=4, color='red', symbol='circle'),
            name='Center Point'
        ))
        # print("false")

    # Add actuators
    for i in range(6):
        
        fig.add_trace(go.Scatter3d(
            x=[base_x[i], top_points_rotated[0][i]],
            y=[base_y[i], top_points_rotated[1][i]],
            z=[base_z[i], top_points_rotated[2][i]],
            mode='lines',
            line=dict(color='red', width=4),
            name=f'Actuator {i + 1}',
        ))

    # Print the x, y, z coordinates of each actuator's endpoints
    # print("Actuator endpoints:")
    # for i in range(6):
    #     base_coords = (base_x[i], base_y[i], base_z[i])
    #     top_coords = (top_points_rotated[0][i], top_points_rotated[1][i], top_points_rotated[2][i])
    #     print(f"Actuator {i + 1}: Base {base_coords}, Top {top_coords}")


    # Update layout
    fig.update_layout(
    scene=dict(
        xaxis=dict(range=[-1000, 1000]),
        yaxis=dict(range=[-1000, 1000]),
        zaxis=dict(range=[0, 1500]),
        # camera=dict(
        #     eye=dict(x=0, y=2, z=0),  # Change these values to adjust the viewing angle
        #     up=dict(x=0, y=0, z=1)          # Specify the "up" direction
        # )
    ),
    title="Custom Stewart Platform Simulation",
)


    return fig



def get_input_from_terminal():
    global latest_input
    while True:
        random_value = random.randint(0, 100)
        coordinates[0] = random_value


# Routes onward
# initail route / figure
@app.route('/')
def index():
    print(request.host);
    # Create the default plot
    fig = create_stewart_platform()
    plot_div = fig.to_html(full_html=False)
    return render_template('index.html', plot_div=plot_div , ip=request.host)


@app.route('/update_plot', methods=['POST'])
def update_plot():
    try:
        if(elements[0] != float(request.form.get('offset_x' , 0))):
            print("Updated:offset_x "+ request.form.get('offset_x' , 0))
        elif(elements[1] != float(request.form.get('offset_y' , 0))):
            print("Updated:offset_y "+ request.form.get('offset_y' , 0))
        elif(elements[2] != float(request.form.get('offset_z' , 0))):
            print("Updated:offset_z "+ request.form.get('offset_z' , 0))
        elif(elements[3] != float(request.form.get('roll' , 0))):
            print("Updated:roll "+ request.form.get('roll' , 0))
        elif(elements[4] != float(request.form.get('pitch' , 0))):
            print("Updated:pitch "+ request.form.get('pitch' , 0))
        elif(elements[5] != float(request.form.get('rotation' , 0))):
            print("Updated:rotation "+ request.form.get('rotation' , 0))
        elif(elements[6] != float(request.form.get('act_1' , 0))):
            print("Updated:act_1 "+ request.form.get('act_1' , 0))
        elif(elements[7] != float(request.form.get('act_2' , 0))):
            print("Updated:act_2 "+ request.form.get('act_2' , 0))
        elif(elements[8] != float(request.form.get('act_3' , 0))):
            print("Updated:act_3 "+ request.form.get('act_3' , 0))
        elif(elements[9] != float(request.form.get('act_4' , 0))):
            print("Updated:act_4 "+ request.form.get('act_4' , 0))
        elif(elements[10] != float(request.form.get('act_5' , 0))):
            print("Updated:act_5 "+ request.form.get('act_5' , 0))
        elif(elements[11] != float(request.form.get('act_6' , 0))):
            print("Updated:act_6 "+ request.form.get('act_6' , 0))

        elements[0] = float(request.form.get('offset_x' , 0))
        elements[1] = float(request.form.get('offset_y' , 0))
        elements[2] = float(request.form.get('offset_z' , 0))
        elements[3] = float(request.form.get('roll' , 0))
        elements[4] = float(request.form.get('pitch' , 0))
        elements[5] = float(request.form.get('rotation' , 0))
        elements[6] = float(request.form.get('act_1' , 0))
        elements[7] = float(request.form.get('act_2' , 0))
        elements[8] = float(request.form.get('act_3' , 0))
        elements[9] = float(request.form.get('act_4' , 0))
        elements[10] = float(request.form.get('act_5' , 0))
        elements[11] = float(request.form.get('act_6' , 0))
        

    
        offset_x = float(request.form.get('offset_x', 0))
        offset_y = float(request.form.get('offset_y', 0))
        offset_z = float(request.form.get('offset_z', 0))
        roll = float(request.form.get('roll', 0)) #yaw=roll , pitch=pitch
        pitch = float(request.form.get('pitch', 0))
        rotation = float(request.form.get('rotation', 0))
        act_1 = float(request.form.get('act_1' , 0))
        act_2 = float(request.form.get('act_2' , 0))
        act_3 = float(request.form.get('act_3' , 0))
        act_4 = float(request.form.get('act_4' , 0))
        act_5 = float(request.form.get('act_5' , 0))
        act_6 = float(request.form.get('act_6' , 0))
        dgc = request.form.get('dgc' , False)

        act_value = [act_1,act_2,act_3,act_4,act_5,act_6]

        # print("x:" , offset_x , " y:" , offset_y)
        # print("rotation:" , rotation , " y:" , offset_y)

        # Create the updated plot
        fig = create_stewart_platform(offset_x, offset_y, offset_z, roll , pitch , rotation , act_value , dgc)
        fig_html = fig.to_html(full_html=False)

        return jsonify({'plot_html': fig_html})
    except ValueError:
        return jsonify({'error': 'Invalid input values'}), 400

@app.route('/update_from_serial', methods=['GET'])
def update_from_serial():
    global coordinates
    # Update the plot using the latest `coordinates` from the serial data
    fig = create_stewart_platform(
        offset_x=coordinates[0],
        offset_y=coordinates[1],
        offset_z=coordinates[2],
        roll=coordinates[3],
        pitch=coordinates[4],
        rotation=coordinates[5]
    )
    fig_html = fig.to_html(full_html=False)
    return jsonify({'plot_html': fig_html})

@app.route('/get_coordinates', methods=['GET'])
def get_coordinates():
    random_value = random.randint(0, 100)
    coordinates[0] = random_value
    return jsonify({'coordinates': coordinates})

@app.route('/get_distance', methods=['GET'])
def get_distance():
    return jsonify({'distance': distance})

@app.route('/get_logs', methods=['GET'])
def get_logs():
    return jsonify({'logs': logs})

@app.route('/get-value', methods=['GET'])
def get_value():
    return jsonify(latest_input)
@app.route('/update_dgc', methods=['POST'])
def update_dgc():
    log = request.form.get('dgc' , "abc")
    print("Drill gun control clicked " + log)
    return jsonify({'status': 'success'})
@app.route('/connect', methods=['POST'])
def connect():
    print("Connected")
    return jsonify({'status': 'success'})
@app.route('/disconnect', methods=['POST'])
def disconnect():
    print("Disconnected")
    return jsonify({'status': 'success'})
@app.route('/calibrate', methods=['POST'])
def calibrate():
    print("Homing Position")
    return jsonify({'status': 'success'})
@app.route('/normal_control', methods=['POST'])
def normal_control():
    print("Normal control clicked "+request.form.get('nc' , "abc"))
    return jsonify({'status': 'success'})
@app.route('/pid_control', methods=['POST'])
def pid_control():
    print("PID control clicked " + request.form.get('pc' , "abc"))
    return jsonify({'status': 'success'})
@app.route('/joystick_control', methods=['POST'])
def joystick_control():
    log = request.form.get('jc' , "abc")
    print("Joystick control clicked "+log)
    return jsonify({'status': 'success'})
@app.route('/wave_action', methods=['POST'])
def wave_action():
    log = request.form.get('wa' , "abc")
    print("Wave action clicked " + log)
    return jsonify({'status': 'success'})
@app.route('/teach', methods=['POST'])
def teach():
    log = request.form.get('teach' , "abc")
    log2 = request.form.get('end' , "false")
    print("Teach clicked " + log +" "+log2)
    return jsonify({'status': 'success'})

if __name__ == "__main__":
    # input_thread = threading.Thread(target=get_input_from_terminal, daemon=True)
    # input_thread.start()
    app.run(host="0.0.0.0", port=5000, debug=True)