import * as d3 from "d3"
import $ from 'jquery';

class Sim6D{
    constructor(layout,svg, g){
        this.layout = layout;
        this.svg = null;
        this.g = null;
        this.numRows = null;
        this.numColumns = null;
        this.columnInterval = null;
        this.rowInterval = null;
        this.stations = null;
        this.shuttles = null;
        this.order = null;
        this.pos = {x: null, y: null};
    }

    resetSimulation(){
        d3.selectAll("svg").remove();
    }

    drawGrid(){
    // Add the grid
    for (let i = 1; i < this.numRows; i++){
        const currenty =  this.rowInterval * i;
        this.g.append('line')
          .style("stroke", "#7f8c8d")
          .style("stroke-width", 1)
          .attr("x1", 0)
          .attr("y1", currenty)
          .attr("x2", (this.columnInterval * this.numColumns))
          .attr("y2", currenty); 
      }
  
      for (let i = 1; i < this.numColumns; i++){
        const currentx =  this.columnInterval * i;
        this.g.append('line')
          .style("stroke", "#7f8c8d")
          .style("stroke-width", 1)
          .attr("x1", currentx)
          .attr("y1", 0)
          .attr("x2", currentx)
          .attr("y2", (this.rowInterval * this.numRows)); 
      }
    }
    getColor(color){
        if (color === 'green') return '#2ecc71';
        else if (color === 'blue') return '#3498db';
        else if (color === 'red') return '#e74c3c';
        else return color;
    }

    drawStations(){
        // https://flatuicolors.com/palette/defo


        for (let i = 0; i < this.stations.length; i++){
            const station = this.stations[i];
            if (!station.stationType) continue;
            if (!station.stationType.color || station.stationType.color === "grey") continue;

            // CurrentRow and currentCol is the row and color index (0,0 is the bottom left), if the index of the station is sorted the same way
            const currentRow = this.numRows - station.position.y - 1; 
            const currentCol = station.position.x;
            
            const currentx = currentCol  * this.rowInterval + this.rowInterval / 2;
            const currenty = currentRow * this.columnInterval + this.columnInterval / 2;

            const marginFactor = 0.8;
            const r = (this.columnInterval / 2 * marginFactor);  
      
            // https://flatuicolors.com/palette/defo
            this.g.append("circle")
              .attr('id', station.id)
              .attr("cx", currentx)
              .attr("cy", currenty)
              .attr("fill", this.getColor(station.stationType.color))
              .attr("r", r)
            
        } 
    }

    generateShadow(){
        // Just a simple svg filter to generate shadow
        var defs = this.svg.append("defs");

        var filter = defs.append("filter")
            .attr("id", "drop-shadow")
            .attr("height", "130%");
    
            filter.append("feGaussianBlur")
            .attr("in", "SourceAlpha")
            .attr("stdDeviation", 3)
            .attr("result", "blur");
        filter.append("feOffset")
            .attr("in", "blur")
            .attr("dx", 2)
            .attr("dy", 2)
            .attr("result", "offsetBlur")
        filter.append("feFlood")
            .attr("in", "offsetBlur")
            .attr("flood-color", "#3d3d3d")
            .attr("flood-opacity", "0.5")
            .attr("result", "offsetColor");
        filter.append("feComposite")
            .attr("in", "offsetColor")
            .attr("in2", "offsetBlur")
            .attr("operator", "in")
            .attr("result", "offsetBlur");
    
        var feMerge = filter.append("feMerge");
    
        feMerge.append("feMergeNode")
            .attr("in", "offsetBlur")
        feMerge.append("feMergeNode")
            .attr("in", "SourceGraphic");
    }

    drawShuttles(){
        let shuttles = this.shuttles;

        // Margin in percent, how much of a rectangle the shuttle fills
        var shuttleDim = {marginPercent: 70};

        // The size of the shuttle is dynamic, depending column and row interval, depending on the grid size
        let shuttleSize = {width: this.columnInterval * (shuttleDim.marginPercent / 100.0), height: this.rowInterval * (shuttleDim.marginPercent / 100.0) };
        let ShuttleMarginPx = {x: (this.columnInterval - shuttleSize.width) / 2, y: (this.rowInterval - shuttleSize.height) / 2};
 
        for (let i = 0; i < shuttles.length; i++){

            let currentShuttle = shuttles[i];
      
            let shuttleG = this.g.append("g")
              .attr("id", "shuttle_" + i);
      
            shuttleG.append("rect")
                .attr("class", "shuttleClass")
                .attr("x", ShuttleMarginPx.x)
                .attr("y", ShuttleMarginPx.y)
                .attr("width", shuttleSize.width)
                .attr("height", shuttleSize.height)
                .attr("stroke", "#7f8c8d")
                .attr("stroke-width", 4)
                .style("filter", "url(#drop-shadow)")
                .attr("rx", 8)
                .attr("fill", "#dcdde1");
        
            shuttleG.append("text")
                .text(currentShuttle.id)
                .attr("x", this.columnInterval / 2)
                .attr("y", this.rowInterval / 2)
                .attr("text-anchor", "middle");

            // Calculate the shuttle dransform. Start from the bottom left, and move right
            let shuttlePos = {x: currentShuttle.position.x * this.columnInterval, y: (this.rowInterval * (this.numRows - 1) - (currentShuttle.position.y * this.rowInterval))}
    
            currentShuttle.pos = shuttlePos; //{x: i, y: 0};

            shuttleG 
              .attr("transform", "translate(" + shuttlePos.x + " ," + shuttlePos.y + ")");
            
          }
    }

    initialize6D(initData) {

        const initDataOK = initData.rows !== 0 && initData.columns !== 0;
        if (!initDataOK) return;

        const rx = 15;  // Rounded edge of the board

        //extend data ugly way - NOT SO GOOD
        let data = JSON.parse(JSON.stringify(initData));

        this.resetSimulation();

        // Calculate the row and column interval
        this.numRows = data.rows;
        this.numColumns = data.columns;
        this.stations = data.stations;
        this.order = data.order;
        this.shuttles = data.shuttles;

        this.rowInterval = this.columnInterval = Math.min(this.layout.height / this.numRows, this.layout.width/this.numColumns);

        this.data = data;

        // Initialization. Add the svg element and the g warpper, wrapping all the svg elements, including the outer transforms
        this.svg = d3
            .select("#d3-main")
            .append("svg")
            .attr("width", this.layout.width + this.layout.margin.left + this.layout.margin.right)
            .attr("height", this.layout.height + this.layout.margin.top + this.layout.margin.bottom);

        // Wraper around everything
        this.g = this.svg.append("g")
            .attr("id","gBoard")
            .attr("transform", "translate(" + this.layout.margin.left + "," + this.layout.margin.top + ")");
            
        
        this.generateShadow();
        // Append the outer rectangle
        this.g.append('rect')
            .attr('x', 0)
            .attr('y', 0)
            .attr('fill', 'white')
            .attr('width', (this.columnInterval * this.numColumns))
            .attr('height', (this.rowInterval * this.numRows))
            .attr('stroke-width', 1)
            .style("filter", "url(#drop-shadow)")
            .attr('stroke', "#95a5a6")
            .attr('stroke-opacity', 0.2)
            .attr('fill', '#f5f6fa')
            .attr('rx', rx)

        let shuttleStartG = this.g.append('g')
            .attr('id','gStartingStation')
            .attr('transform', 'translate(0,0)');

        const startAndReturnPath = `M${rx},0 h ${this.columnInterval * this.numColumns - 2 * rx} q${rx},0 ${rx},${rx}
        v${this.rowInterval * this.numRows - 2 * rx} q0,${rx} ${-rx},${rx}
        h${- (this.columnInterval * this.numColumns - 2 * rx)}
        q${-rx},0 ${-rx},${-rx}
        v${-this.rowInterval + rx}
        h${this.columnInterval * (this.numColumns - 1)}
        v${-(this.rowInterval * (this.numRows - 2))}
        h${-(this.columnInterval * (this.numColumns - 1))}
        v${-this.rowInterval + rx}
        q0,${-rx} ${rx},${-rx}`
    
        ;
        
        shuttleStartG.append("path")
            .attr("id", "line")
            .attr("d", startAndReturnPath)
            .attr("fill", "#d1ccc0")
        

        this.drawGrid();
        this.drawStations();
        // this.drawTables();
        this.drawShuttles();
    }

    moveShuttle(id, pos, duration){
        let currentShuttle = this.shuttles.find(x => x.id === id);

        if (currentShuttle){
            let shuttleEl = d3.select("#shuttle_" + id);

            currentShuttle.pos = pos;
        
            shuttleEl.transition()
                .duration(duration)
                .attr("transform", "translate(" + (pos.x * this.columnInterval).toString()  + "," + (((this.numRows - 1) * this.rowInterval) - (pos.y * this.rowInterval)).toString()+ ")");
        }else{
            console.log("No shuttle found with id: " + id)
        }

    }

    setProcessingStationColor (id, color) {
        let stationEl = d3.select("#" + id);
        stationEl.attr("fill", this.getColor(color))
    }
}

export default Sim6D;
