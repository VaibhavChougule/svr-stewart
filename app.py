from flask import Flask, render_template_string, render_template, request ,jsonify
import numpy as np
import plotly.graph_objects as go

app = Flask(__name__)

# Predefined platform points
base_points = {
    0: (-0.14, -0.13),
    1: (-0.19, -0.06),
    2: (-0.04, 0.195),
    3: (0.04, 0.195),
    4: (0.19, -0.06),
    5: (0.14, -0.13)
}

top_points = {
    0: (-0.04, -0.19),
    1: (-0.19, 0.060),
    2: (-0.14, 0.134),
    3: (0.14, 0.134),
    4: (0.19, 0.060),
    5: (0.04, -0.19)
}

# Extract coordinates
base_x = [p[0] for p in base_points.values()]
base_y = [p[1] for p in base_points.values()]
base_z = [0] * len(base_x)  # Base height is 0

top_x = [p[0] for p in top_points.values()]
top_y = [p[1] for p in top_points.values()]
top_z = [5] * len(top_x)  # Top height is 5


# Function to create a 3D Stewart Platform plot
def create_stewart_platform(offset_x=0, offset_y=0, offset_z=0, rotation=0):
    print("xxxxxxxxxx")
    # Apply offsets and rotation to the top platform
    rotation_matrix = np.array([
        [np.cos(rotation), -np.sin(rotation), 0],
        [np.sin(rotation), np.cos(rotation), 0],
        [0, 0, 1],
    ])
    top_points_rotated = np.dot(
        rotation_matrix,
        np.vstack((top_x, top_y, np.array(top_z) + offset_z))
    )
    top_points_rotated[0] += offset_x
    top_points_rotated[1] += offset_y

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

    # Add actuators
    for i in range(6):
        fig.add_trace(go.Scatter3d(
            x=[base_x[i], top_points_rotated[0][i]],
            y=[base_y[i], top_points_rotated[1][i]],
            z=[base_z[i], top_points_rotated[2][i]],
            mode='lines',
            line=dict(color='red', width=4),
            name=f'Actuator {i + 1}'
        ))

    # Update layout
    fig.update_layout(
        scene=dict(
            xaxis=dict(range=[-0.3, 0.3]),
            yaxis=dict(range=[-0.3, 0.3]),
            zaxis=dict(range=[-0.3, 6]),
        ),
        title="Custom Stewart Platform Simulation",
    )

    return fig


# Routes onward
# initail route / figure
@app.route('/')
def index():
    # Create the default plot
    fig = create_stewart_platform()
    plot_div = fig.to_html(full_html=False)
    return render_template('index.html', plot_div=plot_div)


@app.route('/update_plot', methods=['POST'])
def update_plot():
    try:
        offset_x = float(request.form.get('offset_x', 0))
        offset_y = float(request.form.get('offset_y', 0))
        offset_z = float(request.form.get('offset_z', 0))
        rotation = float(request.form.get('rotation', 0))

        print("x:" , offset_x , " y:" , offset_y)

        # Create the updated plot
        fig = create_stewart_platform(offset_x, offset_y, offset_z, rotation)
        fig_html = fig.to_html(full_html=False)

        return jsonify({'plot_html': fig_html})
    except ValueError:
        return jsonify({'error': 'Invalid input values'}), 400






if __name__ == "__main__":
    app.run(host="0.0.0.0", port=5000, debug=True)