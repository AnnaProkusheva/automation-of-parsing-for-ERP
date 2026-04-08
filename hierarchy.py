class Node:
    def __init__(self, name):
        self.name = name      # Имя узла (например, "Цех 1")
        self.children = []    # Список детей (то, что внутри)

    def add_child(self, child_node):
        self.children.append(child_node)

def visualize_hierarchy(node, level=0):
    # Печатаем имя с отступом. Чем глубже уровень, тем больше отступ.
    indent = "  " * level
    print(f"{indent}└── {node.name}")

    # Рекурсия: для каждого ребенка запускаем эту же функцию
    for child in node.children:
        visualize_hierarchy(child, level + 1)

# 1. Создаем корневой элемент
root = Node("Завод 'Прометей'")

# 2. Создаем цеха
shop_1 = Node("Цех №1 (Механический)")
shop_2 = Node("Цех №2 (Сборочный)")

# 3. Создаем оборудование
pump_1 = Node("Насос Гном 40-25")
pump_2 = Node("Насос Гном 10-10")
machine_1 = Node("Станок токарный")

# 4. Строим связи (Кто кому родитель)
root.add_child(shop_1)
root.add_child(shop_2)

shop_1.add_child(pump_1)
shop_1.add_child(pump_2)
shop_2.add_child(machine_1)

# 5. Запускаем визуализацию
print("Структура оборудования:")
visualize_hierarchy(root)