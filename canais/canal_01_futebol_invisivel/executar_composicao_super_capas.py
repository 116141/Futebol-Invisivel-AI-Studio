import os
import sys

sys.path.append(os.path.abspath("canais/canal_01_futebol_invisivel"))
import compor_super_capas_alto_ctr as c

raw_paqueta = r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\5e1c595d-f303-4a2c-93b1-dcaaf7304f16\raw_paqueta_super_ctr_1792828955391.jpg"
out_paqueta = os.path.abspath("canais/canal_01_futebol_invisivel/videos_prontos/documentarios_longos/CAPA_IMPECAVEL_PAQUETA_BANIMENTO_CTR_MAXIMO.jpg")

raw_clasico = r"C:\Users\Uni-CvFCT-EdmilsonGi\.gemini\antigravity\brain\5e1c595d-f303-4a2c-93b1-dcaaf7304f16\raw_el_clasico_super_ctr_1792828961015.jpg"
out_clasico = os.path.abspath("canais/canal_01_futebol_invisivel/videos_prontos/documentarios/CAPA_IMPECAVEL_EL_CLASICO_UEFA_CTR_MAXIMO.jpg")

print("Compondo capa do Paquetá...")
c.compor_capa_paqueta(raw_paqueta, out_paqueta)

print("Compondo capa do El Clásico...")
c.compor_capa_el_clasico(raw_clasico, out_clasico)

print("Concluído!")
