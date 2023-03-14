module.exports = class Semaphore {

    constructor (max) {
        this.max = max;
        this.counter = 0;
        this.waiting = [];

    }

    take () {
      if (this.waiting.length > 0 && this.counter < this.max){
        this.counter++;
        let promise = this.waiting.shift();
        promise.resolve();
      }
    }
    
    acquire () {
        // console.log('acquiring new semaphore', this.counter, 'out of', this.max)
      if(this.counter < this.max) {
        this.counter++
        return new Promise(resolve => {
        resolve();
      });
      } else {
        return new Promise((resolve, err) => {
            this.waiting.push({resolve: resolve, err: err});
        });
      }
    }
      
    release () {
        // console.log('releasing semaphore', this.counter, 'out of', this.max)
     this.counter--;
     this.take();
    }
    
    purge () {
      let unresolved = this.waiting.length;
    
      for (let i = 0; i < unresolved; i++) {
        this.waiting[i].err('Task has been purged.');
      }
    
      this.counter = 0;
      this.waiting = [];
      
      return unresolved;
    }
  }