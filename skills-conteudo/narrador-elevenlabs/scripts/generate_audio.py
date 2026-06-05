#!/usr/bin/env python3
"""
Narrador ElevenLabs - Script de Geração de Áudio
Lex Intelligentia

Converte roteiros de vídeo (coluna Áudio) em arquivos de áudio MP3
usando a API do ElevenLabs.

Uso:
    python3 generate_audio.py --input roteiro.txt --output narration.mp3
    python3 generate_audio.py --input roteiro.txt --output narration.mp3 --voice "Antoni"
"""

import os
import sys
import argparse
import re


def clean_script_for_narration(raw_text: str) -> str:
    """
    Remove marcações de tempo, instruções visuais e formatação,
    deixando apenas o texto limpo para narração.
    """
    lines = raw_text.strip().split("\n")
    narration_parts = []

    for line in lines:
        # Remove timestamps como [0-3s], [3-7s], etc.
        line = re.sub(r"\[\d+[–-]\d+s?\]", "", line)
        # Remove prefixos como "Voz:" ou "Áudio:"
        line = re.sub(r"^(Voz|Áudio|Audio)\s*:\s*", "", line.strip())
        # Remove instruções visuais (linhas que começam com "Visual:" ou "On-screen:")
        if re.match(r"^(Visual|On-screen|Fundo|Cabeçalho|Efeito|Animação|CTA|Style)", line.strip()):
            continue
        # Remove linhas vazias e separadores
        if line.strip() and line.strip() != "|":
            narration_parts.append(line.strip())

    # Junta com pausas naturais entre blocos
    return " <break time=\"0.5s\" /> ".join(narration_parts)


def generate_audio(text: str, output_path: str, voice_id: str = None, model_id: str = "eleven_multilingual_v2"):
    """
    Gera áudio usando a API do ElevenLabs.
    """
    try:
        from elevenlabs import ElevenLabs
    except ImportError:
        print("ERRO: Instale o SDK do ElevenLabs: pip install elevenlabs")
        sys.exit(1)

    api_key = os.environ.get("ELEVENLABS_API_KEY")
    if not api_key:
        print("ERRO: Variável de ambiente ELEVENLABS_API_KEY não definida.")
        sys.exit(1)

    client = ElevenLabs(api_key=api_key)

    # Se não especificou voice_id, usar uma voz padrão masculina brasileira
    if not voice_id:
        # Listar vozes disponíveis e escolher uma adequada
        voices = client.voices.get_all()
        # Tentar encontrar uma voz masculina em português
        voice_id = None
        for voice in voices.voices:
            if "portuguese" in (voice.labels or {}).get("language", "").lower() or \
               "brazilian" in (voice.labels or {}).get("accent", "").lower():
                voice_id = voice.voice_id
                print(f"Voz selecionada: {voice.name} ({voice.voice_id})")
                break
        # Fallback para voz padrão
        if not voice_id:
            voice_id = "pNInz6obpgDQGcFmaJgB"  # Adam (voz padrão)
            print(f"Usando voz padrão: Adam ({voice_id})")

    print(f"Gerando áudio ({len(text)} caracteres)...")
    print(f"Modelo: {model_id}")
    print(f"Voice ID: {voice_id}")

    audio = client.text_to_speech.convert(
        text=text,
        voice_id=voice_id,
        model_id=model_id,
        voice_settings={
            "stability": 0.6,        # Estabilidade moderada (tom professoral)
            "similarity_boost": 0.8,  # Alta fidelidade à voz original
            "style": 0.3,            # Pouco estilo (evita exageros)
            "use_speaker_boost": True
        }
    )

    # Salvar o áudio
    with open(output_path, "wb") as f:
        for chunk in audio:
            f.write(chunk)

    print(f"Áudio salvo em: {output_path}")
    return output_path


def main():
    parser = argparse.ArgumentParser(description="Narrador ElevenLabs - Lex Intelligentia")
    parser.add_argument("--input", "-i", required=True, help="Arquivo de roteiro (texto)")
    parser.add_argument("--output", "-o", required=True, help="Arquivo de saída (MP3)")
    parser.add_argument("--voice", "-v", default=None, help="Voice ID do ElevenLabs")
    parser.add_argument("--model", "-m", default="eleven_multilingual_v2", help="Modelo de TTS")
    parser.add_argument("--raw", action="store_true", help="Não limpar o texto (enviar como está)")

    args = parser.parse_args()

    # Ler o roteiro
    with open(args.input, "r", encoding="utf-8") as f:
        raw_text = f.read()

    # Limpar o texto para narração (a menos que --raw)
    if args.raw:
        narration_text = raw_text
    else:
        narration_text = clean_script_for_narration(raw_text)

    print(f"--- Texto para narração ---")
    print(narration_text[:500] + "..." if len(narration_text) > 500 else narration_text)
    print(f"---")

    # Gerar áudio
    generate_audio(
        text=narration_text,
        output_path=args.output,
        voice_id=args.voice,
        model_id=args.model
    )


if __name__ == "__main__":
    main()
