# Se importan las librerías necesarias
from mesa import Agent, Model
from mesa.space import SingleGrid
from mesa.time import RandomActivation
import numpy as np

# --- Se importa Flask para crear el servidor ---
from flask import Flask, jsonify

# =============================================================================
# DEFINICIÓN DEL MODELO Y AGENTE
# =============================================================================

class FoodCollector(Agent):
    def __init__(self, unique_id, model):
        self.unique_id = unique_id
        self.model = model
        self.pos = None
        self.energy_units = 100
        self.has_food = False

    def move(self):
        possible_positions = self.model.grid.get_neighborhood(self.pos, moore=False, include_center=False)
        options = np.random.permutation(len(possible_positions))
        for i in options:
            position = possible_positions[i]
            if self.model.grid.is_cell_empty(position):
                self.model.grid.move_agent(self, position)
                self.energy_units -= 1
                break

    def move_towards_base(self):
        base_pos = (5, 5)
        dx = base_pos[0] - self.pos[0]
        dy = base_pos[1] - self.pos[1]
        if abs(dx) > abs(dy):
            next_x = self.pos[0] + np.sign(dx)
            next_y = self.pos[1]
        else:
            next_x = self.pos[0]
            next_y = self.pos[1] + np.sign(dy)
        next_pos = (int(next_x), int(next_y))
        if self.model.grid.is_cell_empty(next_pos):
            self.model.grid.move_agent(self, next_pos)
            self.energy_units -= 1
        else:
            self.move()

    def step(self):
        if self.has_food:
            if self.pos == (5, 5):
                self.has_food = False
                self.energy_units = 100
            else:
                self.move_towards_base()
        else:
            (x, y) = self.pos
            if self.model.cells[x][y] == 1:
                self.model.cells[x][y] = 0
                self.has_food = True
            else:
                self.move()

class FoodCollectorModel(Model):
    def __init__(self, width, height, agents, food):
        super().__init__()
        self.grid = SingleGrid(width, height, torus=True)
        self.schedule = RandomActivation(self)
        self.cells = np.zeros((width, height))
        self.cells[5][5] = -1

        food_placed = 0
        while food_placed < food:
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            if self.cells[x][y] == 0:
                self.cells[x][y] = 1
                food_placed += 1

        agents_placed = 0
        while agents_placed < agents:
            x = self.random.randrange(width)
            y = self.random.randrange(height)
            if self.grid.is_cell_empty((x, y)) and self.cells[x][y] == 0:
                agent = FoodCollector(agents_placed, self)
                self.grid.place_agent(agent, (x, y))
                self.schedule.add(agent)
                agents_placed += 1

    def step(self):
        self.schedule.step()
    def is_finished(self):
        """ Retorna True si ya no hay comida en la cuadrícula. """
        return not np.any(self.cells == 1)

# =============================================================================
# CONFIGURACIÓN DEL SERVIDOR FLASK
# =============================================================================

# --- Configuración inicial de la simulación ---
WIDTH = 11
HEIGHT = 11
AGENTS = 5
FOOD = 20

# --- Se crea una instancia global del modelo ---
model = FoodCollectorModel(WIDTH, HEIGHT, AGENTS, FOOD)

# --- Se crea la aplicación Flask ---
app = Flask(__name__)


def get_simulation_data():
    """ Función para recolectar y formatear los datos en JSON """
    agent_data = []
    for agent in model.schedule.agents:
        agent_data.append({
            "id": agent.unique_id,
            "x": agent.pos[0],
            "y": agent.pos[1],
            "has_food": agent.has_food
        })
        
    food_data = []
    for x in range(model.grid.width):
        for y in range(model.grid.height):
            if model.cells[x][y] == 1:
                food_data.append({"x": x, "y": y})
                
    return {
        "is_finished": model.is_finished(), 
        "agents": agent_data, 
        "food": food_data
    }

# --- Se definen las rutas (endpoints) de la API ---

@app.route('/')
def index():
    return "¡Servidor de simulación funcionando!"

@app.route('/step', methods=['GET'])
def simulation_step():
    """
    Este endpoint es el que llamará Unity.
    Avanza un paso en la simulación y devuelve el estado del mundo.
    """
    if not model.is_finished():
        model.step()
    
    data = get_simulation_data()
    return jsonify(data)
# --- Punto de entrada para ejecutar el servidor ---
if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5000, debug=True)