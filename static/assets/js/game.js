class Game {
    constructor() {
      this.players = {
        player1: null,
        player2: null
      };
      this.maxPlayers = 2;
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
  }
  