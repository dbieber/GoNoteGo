const Form = ({ fields }) => {
  return (
    <form action="/submit" method="post" className="form">
      {fields.map(field => (
        <div className="form-group" key={field.id}>
          <label htmlFor={field.id}>{field.label}:</label>
          <input 
              type={field.type} 
              id={field.id} 
              name={field.name} 
              defaultValue={field.value}
          />
        </div>
      ))}
      <input type="submit" value="Submit" className="submit-button" />
    </form>
  );
};
