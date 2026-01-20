import pygame
import xml.etree.ElementTree as ET
import sys
import math

# --- PROJECT AXIOGEN: WORLD LOADER v0.2 ---

class World:
    def __init__(self, xml_file):
        self.tree = ET.parse(xml_file)
        self.root = self.tree.getroot()
        self.width = int(self.root.get('width', 800))
        self.height = int(self.root.get('height', 600))
        
        # Physics settings
        physics_params = self.root.find('physics')
        self.friction = float(physics_params.get('friction', 0.95))
        
        self.foods = []
        self.obstacles = []
        
        for entity in self.root.find('entities'):
            if entity.tag == 'food':
                self.foods.append({
                    'x': int(entity.get('x')), 
                    'y': int(entity.get('y')), 
                    'energy': int(entity.get('energy'))
                })
            elif entity.tag == 'obstacle':
                self.obstacles.append({
                    'x': int(entity.get('x')), 
                    'y': int(entity.get('y')), 
                    'radius': int(entity.get('radius'))
                })

class Agent:
    def __init__(self, x, y):
        self.x = x
        self.y = y
        self.radius = 15
        self.angle = 0  # Where the agent is facing (0-360)
        self.vel = 0    # Speed
        self.sensors = [] # To store sensor readings

    def move(self, friction):
        # Convert Angle + Speed into X/Y movement (Basic Trigonometry)
        # This is the "Math" the AI will eventually have to learn naturally!
        rad = math.radians(self.angle)
        self.x += math.cos(rad) * self.vel
        self.y += math.sin(rad) * self.vel
        
        # Apply Friction (Slow down if not accelerating)
        self.vel *= friction

    def sense(self, world):
        # 5 Lines of sight (Sensors)
        # Angles: -45, -20, 0, +20, +45 degrees relative to facing direction
        sensor_angles = [-45, -20, 0, 20, 45]
        self.readings = []
        
        for sa in sensor_angles:
            # Calculate the end point of the sensor line (Vision Range = 100px)
            rad = math.radians(self.angle + sa)
            end_x = self.x + math.cos(rad) * 100
            end_y = self.y + math.sin(rad) * 100
            
            # Save the line for drawing
            self.readings.append(((self.x, self.y), (end_x, end_y)))
            
            # (In the next step, we will calculate if these lines hit Food)

    def draw(self, screen):
        # 1. Draw Sensors (The "Eyes") - White Lines
        for start, end in self.readings:
            pygame.draw.line(screen, (100, 100, 100), start, end, 1)

        # 2. Draw Body - Green Circle
        pygame.draw.circle(screen, (0, 255, 0), (int(self.x), int(self.y)), self.radius)
        
        # 3. Draw "Heading" (A red line showing where the nose is)
        nose_x = self.x + math.cos(math.radians(self.angle)) * self.radius
        nose_y = self.y + math.sin(math.radians(self.angle)) * self.radius
        pygame.draw.line(screen, (255, 0, 0), (int(self.x), int(self.y)), (nose_x, nose_y), 2)

def main():
    pygame.init()
    world = World('world_alpha.xml')
    screen = pygame.display.set_mode((world.width, world.height))
    pygame.display.set_caption("Project AXIOGEN - Physics Test")
    clock = pygame.time.Clock()
    
    subject = Agent(world.width // 2, world.height // 2)

    while True:
        screen.fill((20, 20, 20)) # The Void
        
        # --- INPUT HANDLING (Eventually this will be the Neural Network) ---
        keys = pygame.key.get_pressed()
        if keys[pygame.K_LEFT]:
            subject.angle -= 5
        if keys[pygame.K_RIGHT]:
            subject.angle += 5
        if keys[pygame.K_UP]:
            subject.vel += 0.5 # Accelerate
        
        for event in pygame.event.get():
            if event.type == pygame.QUIT:
                pygame.quit()
                sys.exit()

        # --- UPDATE PHYSICS ---
        subject.move(world.friction)
        subject.sense(world)

        # --- DRAW WORLD ---
        for food in world.foods:
            pygame.draw.circle(screen, (255, 255, 0), (food['x'], food['y']), 5)
        for obs in world.obstacles:
            pygame.draw.circle(screen, (255, 50, 50), (obs['x'], obs['y']), obs['radius'])

        subject.draw(screen)
        pygame.display.flip()
        clock.tick(60)

if __name__ == "__main__":
    main()