def patch_interval():
    with open('app/services/autopilot_manager.py', 'r', encoding='utf-8') as f:
        lines = f.readlines()
    
    new_lines = []
    for line in lines:
        if '"intervalo_minutos":' in line:
            new_lines.append('    "intervalo_minutos": 120,        # Cadência econômica: 12 ciclos por dia (a cada 2h) para preservar cota\n')
        else:
            new_lines.append(line)
            
    with open('app/services/autopilot_manager.py', 'w', encoding='utf-8', newline='') as f:
        f.writelines(new_lines)
    print("Sucesso: intervalo atualizado para 120 minutos (2 horas)!")

if __name__ == '__main__':
    patch_interval()
