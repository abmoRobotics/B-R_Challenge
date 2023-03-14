import { atom, useRecoilValue } from "recoil";
import { atConfiguration, atMixData } from '../App';
import { Component } from 'react';
import { Grid } from "@mui/material";
export const atProcessTime = atom({ key: 'processState', default: { startTime: 0, endTime: 0 }});

function Table (props) {

    class TableRow extends Component {
        render() {
            var row = this.props.row;
            return (
                <tr>
                    {row.map(val => <td>{val}</td>)}
                </tr>
            )
        }
    }

    const configuration = useRecoilValue(atConfiguration);
    let { orders, colors } = configuration;
    const  mixData = useRecoilValue(atMixData);
    const processTime = useRecoilValue(atProcessTime);

    
    let tableData = [];
    for (let i = 0; i < orders.length; i++){
        const currentRecipe = orders[i];
        tableData.push([currentRecipe.id]);

        // Fill out the row for the current recipe
        for (let j = 0; j < colors.length; j++){
            const currentColor = colors[j];
            const colorIdxInRecipe = currentRecipe.recipe.findIndex(x => x.color === currentColor);
            if (colorIdxInRecipe !== -1){   // Check if this color is included in the recipe, otherwise the quantity is 0
                tableData[i].push(currentRecipe.recipe[colorIdxInRecipe].quantity);
            }else{
                tableData[i].push(0);
            }
        }
    }
    
    return (
     <>
     <Grid container spacing={2}>
         <Grid item xs={6}>
                <table id="variantTable">
                    <thead>
                    <tr>
                        <th></th>
                        {
                            colors.map((color, idx) => {return(<th key={idx}>{color}</th>)})
                        }
                    </tr>
                    </thead>
                    <tbody>
                        {
                            // They keys in this table just have random strings as keys to avoid errors
                            tableData.map((tableData, idx) => {
                                return <tr key= {(Math.random() + 1).toString(36).substring(2)}>{tableData.map((val) => <td key= {(Math.random() + 1).toString(36).substring(2)}>{val}</td>)}</tr>})
                        }
                    </tbody>
                </table>
            <table id="orderTable">
                <thead>
                    <tr>
                        <th>Mix</th>
                        <th>Quantity</th>
                        <th>Started</th>
                        <th>Finished</th>
                    </tr>
                </thead>
                <tbody>
                {
                    mixData.map((order, idx) => { return(<tr key={idx}><td>{order.id}</td><td>{order.quantity}</td><td>{order.started}</td><td>{order.completed}</td></tr>)})
                }
                </tbody>
            </table>
        </Grid>
         <Grid item xs={6} >
            {
                processTime.endTime !== 0 ?
                    <table id="orderTable">
                        <thead>
                            <tr>
                                <th>Title</th>
                                <th>Value</th>
                            </tr>
                        </thead>
                        <tbody>
                            <tr>
                                <td>
                                    Average Utilization
                                </td>
                                <td>
                                    {processTime.averageUtilization.toFixed(5)}
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    Time score (part 1)
                                </td>
                                <td>
                                    {processTime.timeScore.toFixed(5)}
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    Time score (part 2)
                                </td>
                                <td>
                                    {processTime.timeScoreCellCost.toFixed(5)}
                                </td>
                            </tr>
                            <tr>
                                <td>
                                    -----------
                                </td>
                                <td>
                                    -----------
                                </td>
                            </tr>
                        {
                            Object.entries(processTime.utilizationPerStation).map((data, idx) => { return(<tr key={idx}><td>Station {data[0]}</td><td>{data[1].toFixed(5)}</td></tr>)})
                        }
                        </tbody>
                    </table>
                    : null
            }
            </Grid>
        </Grid>
     </>
    );
  }
  
  export default Table;