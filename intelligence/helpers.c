#include <stdio.h>
#include <stdint.h>
#include <string.h>
#include <time.h>

#include "common.h"
#include "helpers.h"
#include "core.h"

static char piece_chars[7] = {' ','p','r','n','b','q','k'};

void print_state(state_t *state){
    //white pieces are uppper case, black pieces lower case
    printf("------------------\n");
    for (int8_t i = 7; i > -1; i--){
        printf("%d|", i);
        for (int8_t j = 0; j < 8; j++){
            if (state->pieces[i][j] > 0){
                printf("%c|", CHANGE_CASE(piece_chars[state->pieces[i][j]]));
            } else {
                printf("%c|", piece_chars[-state->pieces[i][j]]);
            }
        }
        printf("\n------------------\n");
    }
    printf(" |0|1|2|3|4|5|6|7|\n------------------\n");
}


void print_move(move_t *move){
    printf("move [%d,%d] => [%d,%d], takes: %c, pawn promote? %d\n", \
      move->from[0], move->from[1], move->to[0], move->to[1], \
      move->piece_taken>0?CHANGE_CASE(piece_chars[move->piece_taken]):piece_chars[-move->piece_taken], \
      move->is_pawn_promotion);
}

uint16_t get_time_s(){
    struct timespec cur_time; //*.tv_sec stands for "time value [in] seconds"
    clock_gettime(CLOCK_REALTIME, &cur_time);
    return cur_time.tv_sec;
}

uint16_t str_to_int(uint8_t *string){
    //v. hacky :)
    uint16_t integer = 0;
    uint8_t len = 1;
    uint16_t mul = 1;
    while (string[len] != 0){
        len++;
        mul *= 10;
    }
    uint8_t *p = string;
    while (*p != 0){
        integer += (*p-48) * mul;
        p++;
        mul /= 10;
    }
    return integer;
}

void make_move(state_t *state, move_t *move){
    //note: does not insure move is legal
    int8_t side = state->pieces[MOVE_FROM] > 0 ? WHITE : BLACK;
    if (move->is_pawn_promotion){
        //pawn promotion (auto to queen :)
        state->pieces[MOVE_TO] = side*QUEEN;
        state->pieces[MOVE_FROM] = 0;
    } else {
        //normal move...
        state->pieces[MOVE_TO] = state->pieces[MOVE_FROM];
        state->pieces[MOVE_FROM] = 0;
    }
}

void inverse_move(state_t *state, move_t *move){
    //does the move from to->from
    int8_t side = state->pieces[MOVE_TO] > 0 ? WHITE : BLACK;
    if (move->is_pawn_promotion){
        //pawn promotion (auto to queen :)
        state->pieces[MOVE_TO] = move->piece_taken;
        state->pieces[MOVE_FROM] = side*PAWN;
    } else {
        //normal move...
        state->pieces[MOVE_FROM] = state->pieces[MOVE_TO];
        state->pieces[MOVE_TO] = move->piece_taken;
    }
}

move_t get_user_move_instance(state_t *state, uint8_t fr, uint8_t fc, uint8_t tr, uint8_t tc){
    //creates a move_t instance based on {fr,fc}=>{tr,tc}
    //fills in the piece_taken and is_pawn_promotion attrs. automatically by checking the state
    uint8_t side = state->pieces[fr][fc] > 0 ? WHITE : BLACK;
    move_t player_move = {{fr,fc}, {tr,tc},
                          state->pieces[tr][tc], //piece_taken
                          ABS(state->pieces[tr][tc])==PAWN && tr==BACK_ROW(side)}; //is_pawn_promotion
    return player_move;
}

// the following are NOT used in production...

void print_negamax_route(state_t *state, move_t *best_move, int8_t side, uint8_t depth){
    //To see what negamax had in mind, we sequentially make the best move for the given
    //depth and then decrease the depth by 1 and make the best move for the other side
    //which is what the negamax algorithm works out. At each stage, we print the current state
    move_t move_route[depth];
    printf("analysing negamax's evaluation of the following state, for %s\n", side==WHITE?"white":"black");
    print_state(state);
    int16_t end_score = negamax(state, move_route, side, depth, -INFINITY, INFINITY);
    printf("best eval for %s found, after searching to depth %d, was: %d\n", side==WHITE?"white":"black", depth, end_score);
    printf("~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~~\n");
    printf("Negamax expects the following moves from now:\n");
    //make and print the first move
    print_move(move_route);
    make_move(state, move_route);
    print_state(state);
    //pointer to where to store the next move
    move_t *move_pointer = move_route+1;
    uint8_t d = depth-1;
    while (d > 0){
        //switch perspectives
        side *= -1;
        negamax(state, move_pointer, side, d--, -INFINITY, INFINITY);
        //make the move
        make_move(state, move_pointer);
        print_move(move_pointer);
        print_state(state);
        move_pointer++;
    }
    //iterate over the move_route array backwatds, undoing the moves to reset the state
    move_pointer = move_route+depth;
    while (--move_pointer >= move_route)
    inverse_move(state, move_pointer);
    //copy the best move to their passed in pointer
    if (best_move != NULL)
    memcpy(best_move, move_route, sizeof(move_t));
}

#ifdef DEBUG_NEGAMAX
void copy_state(state_t *in_state, state_t *copy_state){
    memcpy(copy_state, in_state, sizeof(state_t));
}
#endif
