import { format, parseISO } from 'date-fns';

const parseLogMessage = (log) => {
  const { type, workflow_name, timestamp } = log;
  let message = "";

  switch (type) {
    case 'new_workflow':
      message = `You created a new workflow: <span class="workflow-name">${workflow_name}</span>.`;
      break;
    case 'update_workflow':
      message = `You updated the workflow: <span class="workflow-name">${workflow_name}</span>.`;
      break;
    case 'new_user':
      message = 'You joined CrewTailor.';
      break;
    case 'run_workflow':
      message = `You ran the workflow: <span class="workflow-name">${workflow_name}</span>.`;
      break;
    case 'delete_workflow':
      message = `You deleted the workflow: <span class="workflow-name">${workflow_name}</span>.`;
      break;
    case 'add_public_workflow':
      message = `You added workflow: <span class="workflow-name">${workflow_name}</span> from the community.`;
      break;
    default:
      message = 'Unknown action.';
  }

  const formattedTimestamp = format(parseISO(timestamp), 'MMMM d, HH:mm');
  return `${message} - <span class="timestamp">${formattedTimestamp}</span>`;
};

export default parseLogMessage;