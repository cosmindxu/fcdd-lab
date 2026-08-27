export class Chess { constructor(fen){ this.fen=fen; } isCheckmate(){return false;} turn(){return 'w';} isStalemate(){return false;} isInsufficientMaterial(){return false;} }
