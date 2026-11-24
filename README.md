# Gatinho Cavaleiro

Um jogo de plataforma em pixel art feito em Python com pygame.

Você é um gatinho escudeiro. Seu mestre, o cavaleiro, caiu doente por causa de uma maldição antiga. O único remédio é a Raiz Mágica, que brota no fim da floresta, guardada por uma bruxa. Atravesse seis fases, derrote os guardiões do caminho e traga a raiz de volta.

## Como rodar

Você precisa do [Python 3](https://www.python.org/downloads/) e do pygame.

```
pip install -r requirements.txt
python src/main.py
```

Rode os comandos a partir da pasta principal do projeto, com a pasta `assets` ao lado da pasta `src`.

## Controles

| Tecla | Ação |
|---|---|
| Setas ou A / D | Mover |
| Espaço | Pular (e também continuar nos menus e diálogos) |
| J ou X | Golpe de espada |
| K ou Z | Atirar pedra com o estilingue (depois de pegá-lo) |
| E | Falar e examinar (na casa) |
| P | Pausar (a tela de pausa mostra como jogar) |
| R | Reiniciar (na pausa ou ao perder) |
| M | Silenciar |
| F11 | Tela cheia |
| ESC | Pular cenas |

## Modos de jogo

Ao começar, você escolhe o modo com as setas (ou 1, 2 e 3) e confirma com Espaço.

| Modo | Corações no início | Dano que você leva | Vida da bruxa |
|---|---|---|---|
| Fácil | 5 | metade | 14 |
| Normal | 3 | 1 coração | 20 |
| Difícil | 2 | 1,5 coração | 28 |

Os números ficam em `DIFICULDADES`, no começo do `src/main.py`, e podem ser ajustados.

## As fases

1. **O Vilarejo:** moradores pacíficos. Se ferir algum deles, você perde o jogo.
2. **A Estrada:** ladrões e buracos. O líder deles deixa cair o estilingue.
3. **O Cemitério:** zumbis, esqueletos e um esqueleto gigante, que deixa cair a armadura.
4. **A Caverna:** esqueletos no chão
