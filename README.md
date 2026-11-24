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
4. **A Caverna:** esqueletos no chão e morcegos voando no escuro.
5. **As Ruínas do Castelo:** esqueletos de armadura (3 golpes) e um dragão no fim. A alma do dragão é selada na espada.
6. **A Floresta:** lobos que correm atrás de você e a cabana da bruxa, com a Raiz Mágica.

## Dicas

- Cada fase tem 1 coração e 4 pedrinhas para pegar. As pedras acumulam de uma fase para a outra.
- Você pode derrotar inimigos pulando em cima deles ou com a espada.
- A armadura (fase 3) corta o dano que você leva pela metade.
- Com a alma do dragão, o golpe de espada vira um corte de fogo a cada 5 segundos, com 3 de dano.
- As magias da bruxa perseguem você, mas a espada e as pedras as destroem.

## Arquivos

```
src/
  main.py        o jogo inteiro
assets/
  img/           imagens (opcionais)
  sons/          efeitos e músicas
requirements.txt dependências (pygame)
README.md        este arquivo
```

As imagens são opcionais: se alguma não existir, o jogo usa o desenho feito por código no lugar. Sem os sons, o jogo roda em silêncio.

O jogo procura estes arquivos:

- **Imagens (`assets/img`):** `gato_1.png`, `gato_2.png`, `esqueleto_1.png`, `esqueleto_2.png`, `bruxa.png`, `cavaleiro_1.png`, `cavaleiro_2.png`, `cavaleiro_retrato.png` e `gato_menu.png`.
- **Sons (`assets/sons`):** `pulo.wav`, `espada.wav`, `matar.wav`, `dano.wav`, `vitoria.wav`, `derrota.wav`, `texto.wav`, `coracao.wav`, `musica_menu.wav`, `musica_jogo.wav` e `musica_bruxa.wav`.

## Sobre o trabalho

Trabalho desenvolvido para a disciplina de Usabilidade, Desenvolvimento Web, Mobile e Jogos, na Universidade São Judas Tadeu.

- **Professor:** Fabio Tadeu Doro
- **Integrantes:**
  - Nome do integrante 1
  - Nome do integrante 2
  - Nome do integrante 3
