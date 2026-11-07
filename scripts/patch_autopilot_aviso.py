with open("app/services/autopilot_manager.py", "r", encoding="utf-8") as f:
    text = f.read()

# Restaurar intervalo_minutos para 15 minutos
target_intervalo = '"intervalo_minutos": 120,        # Intervalo estendido de 120 minutos (2 horas) entre ciclos'
replacement_intervalo = '"intervalo_minutos": 15,         # Ciclos frequentes (15 min) para produção, manutenção e alertas'

if target_intervalo in text:
    text = text.replace(target_intervalo, replacement_intervalo, 1)

# Inserir chamada de aviso prévio 30 minutos antes do pico
target_scheduler = '            pub_fut = video_scheduler.auto_liberar_videos_se_no_horario_pico("futebol")'
code_aviso = '''            # Aviso Prévio ao Proprietário (30 minutos antes do pico com link para dar uma olhada):
            video_scheduler.enviar_aviso_previo_pico_telegram("futebol", minutos_antecedencia=30)
            video_scheduler.enviar_aviso_previo_pico_telegram("moda", minutos_antecedencia=30)
            video_scheduler.enviar_aviso_previo_pico_telegram("fergil", minutos_antecedencia=30)

            pub_fut = video_scheduler.auto_liberar_videos_se_no_horario_pico("futebol")'''

if target_scheduler in text:
    text = text.replace(target_scheduler, code_aviso, 1)

with open("app/services/autopilot_manager.py", "w", encoding="utf-8") as f:
    f.write(text)

print("SUCCESS: autopilot_manager.py atualizado com aviso prévio e ciclo de 15 min!")
