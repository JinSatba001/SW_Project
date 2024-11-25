class Game {
    constructor() {
      this.players = {
        player1: null,
        player2: null
      };
      this.maxPlayers = 2;
      this.guessHistory = [];  // 추측 기록을 저장할 배열 추가
      this.currentWord = null; // 현재 정답 단어
      this.isStarted = false;  // 게임 시작 여부
    }
  
    addPlayer(playerId, playerName) {
      if (!this.players.player1) {
        this.players.player1 = {
          id: playerId,
          name: playerName
        };
        return true;
      } else if (!this.players.player2) {
        this.players.player2 = {
          id: playerId,
          name: playerName
        };
        return true;
      }
      return false; // 게임이 가득 찼을 때
    }
  
    getPlayerList() {
      return {
        player1: this.players.player1?.name || '대기 중',
        player2: this.players.player2?.name || '대기 중'
      };
    }
  
    removePlayer(playerId) {
      if (this.players.player1?.id === playerId) {
        this.players.player1 = null;
      } else if (this.players.player2?.id === playerId) {
        this.players.player2 = null;
      }
    }
    // 게임 시작
    startGame(word) {
      if (this.players.player1 && this.players.player2) {
          this.currentWord = word;
          this.isStarted = true;
          this.guessHistory = [];
          return true;
      }
      return false;
    }
    // 추측 기록 추가
    addGuess(playerId, guess, similarity) {
      const player = this.getPlayerById(playerId);
      if (!player) return null;

      const guessRecord = {
          playerName: player.name,
          guess: guess,
          similarity: similarity,
          timestamp: new Date().toISOString()
      };

      this.guessHistory.push(guessRecord);
      return guessRecord;
    }
    // 추측 기록 가져오기
    getGuessHistory() {
        return this.guessHistory;
    }

    // 플레이어 ID로 플레이어 찾기
    getPlayerById(playerId) {
        if (this.players.player1?.id === playerId) return this.players.player1;
        if (this.players.player2?.id === playerId) return this.players.player2;
        return null;
    }

    // 게임 상태 확인
    isGameStarted() {
        return this.isStarted;
    }

    // 게임 종료
    endGame() {
        this.isStarted = false;
        this.currentWord = null;
        return this.guessHistory;
    }
}

if (typeof module !== 'undefined' && module.exports) {
  module.exports = Game;
}